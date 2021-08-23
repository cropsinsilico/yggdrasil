from yggdrasil import tools, multitasking
from yggdrasil.communication import RMQComm, NoMessages
from yggdrasil.communication.RMQComm import pika


class RMQAsyncComm(RMQComm.RMQComm):
    r"""Class for handling asynchronous RabbitMQ communications. It is not
    recommended to use this class as it can leave hanging threads if not
    closed propertly. The normal RMQComm will cover most use cases.

    Args:
        name (str): The environment variable where the comm address is stored.
        dont_open (bool, optional): If True, the connection will not be opened.
            Defaults to False.
        **kwargs: Additional keyword arguments are passed to CommBase.

    Attributes:
        times_connected (int): Number of times that this connections has been
            established.
        rmq_thread (multitasking.YggTask): Thread used to run IO loop.

    """
    
    _commtype = 'rmq_async'
    _schema_subtype_description = ('Asynchronous RabbitMQ connection.')
    _disconnect_attr = (RMQComm.RMQComm._disconnect_attr
                        + ['_qres_lock', '_qres_event', 'rmq_thread'])
    
    def _init_before_open(self, **kwargs):
        r"""Initialize null variables and RMQ async thread."""
        self.times_connected = 0
        self.rmq_thread_count = 0
        self.rmq_thread = self.new_run_thread()
        self._opening = False
        self._closing = False
        self._reconnecting = False
        self._close_called = False
        self._buffered_messages = []
        self._qres = None
        self._qres_lock = multitasking.RLock()
        self._qres_event = multitasking.Event()
        self._qres_event.set()
        super(RMQAsyncComm, self)._init_before_open(**kwargs)

    # @classmethod
    # def underlying_comm_class(self):
    #     r"""str: Name of underlying communication class."""
    #     return 'rmq'

    @property
    def rmq_lock(self):
        r"""Lock associated with RMQ ioloop thread."""
        return self.rmq_thread.lock

    def new_run_thread(self, name=None):
        r"""Get a new thread for running."""
        if name is None:
            name = self.name
        self.rmq_thread_count += 1
        return multitasking.YggTask(
            name=name + '.RMQThread%d' % self.rmq_thread_count,
            target=self.run_thread)

    def run_thread(self):
        r"""Connect to the connection and begin the IO loop."""
        self.debug('')
        self.connect()
        self.connection.ioloop.start()
        self.debug("returning")

    def start_run_thread(self):
        r"""Start the run thread and wait for it to finish."""
        with self.rmq_lock:
            if self.rmq_thread.was_started:
                return
            self._opening = True
            self.rmq_thread.start()
        # Wait for connection to be established
        T = self.start_timeout()
        # interval = 1  # timeout / 5
        while (not T.is_out) and (not self.channel_stable) and self.rmq_thread.is_alive():
            self.sleep()  # 0.5 # interval)
        self.stop_timeout()
        # Check that connection was established
        if not self.rmq_thread.is_alive():  # pragma: debug
            self._opening = False
            self.force_close()
            raise Exception("Connection ioloop could not be established.")
        if not self.channel_stable:  # pragma: debug
            self.force_close()
            raise RuntimeError("Connection never finished opening "
                               + "(%f/%f timeout)." % (T.elapsed, T.max_time))

    def bind(self):
        r"""Declare queue to get random new queue."""
        # Start ioloop in a new thread
        with self.rmq_lock:
            # Don't bind if already closing
            if self.is_open or self._close_called:  # pragma: debug
                return
            self._bound = True
        self.start_run_thread()
        # Register queue
        if not self.queue:  # pragma: debug
            self.error("Queue was not initialized.")
        self.register_comm(self.address, (self.connection, self.channel))
        super(RMQComm.RMQComm, self).bind()
    
    def open(self):
        r"""Open connection and bind/connect to queue as necessary."""
        super(RMQAsyncComm, self).open()
        T = self.start_timeout()
        while (not T.is_out) and self._opening:  # pragma: debug
            self.info("Waiting for connection to open")
            self.sleep()
        self.stop_timeout()

    def _close(self, linger=False):
        r"""Close the connection.

        Args:
            linger (bool, optional): If True, drain messages before closing the
                comm. Defaults to False.

        """
        with self.rmq_lock:
            self._close_called = True
            if self._closing:  # pragma: debug
                return  # Don't close more than once
        # Wait for connection to finish opening to close it
        T = self.start_timeout(key=self.timeout_key + '_opening')
        while (not T.is_out) and self._opening:  # pragma: debug
            self.sleep()
        self.stop_timeout(key=self.timeout_key + '_opening')
        # Close by cancelling consumption
        if self.is_open or self._bound:
            with self.rmq_lock:
                self._closing = True
                self._is_open = False
                self._bound = False
                if self.channel is not None:
                    try:
                        if self.direction == 'recv':
                            self.channel.basic_cancel(callback=self.on_cancelok,
                                                      consumer_tag=self.consumer_tag)
                        else:
                            self.channel.close()
                    except (pika.exceptions.ChannelClosed,
                            pika.exceptions.ConnectionClosed,
                            pika.exceptions.ChannelWrongStateError,
                            pika.exceptions.ConnectionWrongStateError):  # pragma: debug
                        self._closing = False
            if not self.is_client:
                self.unregister_comm(self.address)
        # Wait for connection to finish closing & then force if it dosn't
        T = self.start_timeout(key=self.timeout_key + '_closing')
        while (not T.is_out) and self._closing:
            self.sleep()
        self.stop_timeout(key=self.timeout_key + '_closing')
        if self._closing:  # pragma: debug
            self.force_close()
        if self.rmq_thread.is_alive():  # pragma: debug
            self.rmq_thread.join(self.timeout)
            if self.rmq_thread.is_alive():
                raise RuntimeError("Thread still running.")
        # Close workers
        # with self.rmq_lock:
        super(RMQAsyncComm, self)._close(linger=linger)

    def _set_qres(self, res):
        r"""Callback for getting message count."""
        self._qres = res
        self._qres_event.set()

    def get_queue_result(self):
        r"""Get the fram from passive queue declare."""
        res = None
        if self.is_open:
            with self._qres_lock:
                if self._qres_event.is_set():
                    self._qres_event.clear()
                    try:
                        self.channel.queue_declare(queue=self.queue,
                                                   callback=self._set_qres,
                                                   # , auto_delete=True,
                                                   passive=True)
                    except (pika.exceptions.ChannelClosed,
                            pika.exceptions.ConnectionClosed,
                            pika.exceptions.ChannelWrongStateError,
                            pika.exceptions.ConnectionWrongStateError):  # pragma: debug
                        if not self._reconnecting:
                            self._close()
                        else:
                            self._qres = None
                            self._qres_event.set()
            self._qres_event.wait()
            res = self._qres
        return res

    @property
    def n_msg_recv(self):
        r"""int: Number of messages in the queue."""
        if self.is_open:
            return len(self._buffered_messages)
        return 0
        
    def _send(self, msg, exchange=None, routing_key=None, **kwargs):
        r"""Send a message.

        Args:
            msg (str, bytes): Message to be sent.
            exchange (str, optional): Exchange that message should be sent
                to. Defaults to self.exchange.
            routing_key (str, optional): Key that exchange should use to route
                the message. Defaults to self.queue.
            **kwargs: Additional keyword arguments are passed to
                :method:`pika.BlockingChannel.basic_publish`.

        Returns:
            bool: Success or failure of send.

        """
        with self.rmq_lock:
            if self.is_closed:  # pragma: debug
                return False
            out = super(RMQAsyncComm, self)._send(msg, exchange=exchange,
                                                  routing_key=routing_key,
                                                  **kwargs)
        # Basic publish returns None for asynchronous connection
        if out is None:
            out = True
        return out

    def _recv(self):
        r"""Receive a message.

        Returns:
            tuple (bool, obj): Success or failure of receive and received
                message.

        """
        with self.rmq_lock:
            if len(self._buffered_messages) == 0:
                raise NoMessages("No messages in buffer.")
            return (True, self._buffered_messages.pop(0))

    def on_message(self, ch, method, props, body):
        r"""Buffer received messages."""
        body = tools.str2bytes(body)
        if self.direction == 'send':  # pragma: debug
            raise Exception("Send comm received a message.")
        with self.rmq_lock:
            self._buffered_messages.append(body)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    # CONNECTION
    def connect(self):
        r"""Establish the connection."""
        self.times_connected += 1
        parameters = pika.URLParameters(self.url)
        kwargs = dict(on_open_callback=self.on_connection_open,
                      on_open_error_callback=self.on_connection_open_error)
        self.connection = pika.SelectConnection(parameters, **kwargs)

    def on_connection_open(self, connection):
        r"""Actions that must be taken when the connection is opened.
        Add the close connection callback and open the RabbitMQ channel."""
        self.debug('::Connection opened')
        connection.add_on_close_callback(self.on_connection_closed)
        self.open_channel()

    def on_connection_open_error(self, unused_connection, err):  # pragma: debug
        r"""Actions that must be taken when the connection fails to open."""
        self.debug('::Connection could not be opened')
        self.close()
        raise Exception('Could not connect: %s.' % err)

    def on_connection_closed(self, connection, reason):
        r"""Actions that must be taken when the connection is closed. Set the
        channel to None. If the connection is meant to be closing, stop the
        IO loop. Otherwise, wait 5 seconds and try to reconnect."""
        with self.rmq_lock:
            self.info('::on_connection_closed code %s', reason)
            if self._closing or (reason.reply_code == 200):
                connection.ioloop.stop()
                self.connection = None
                self._closing = False
                self._qres_event.set()
            else:
                self.warning('Connection closed, reopening in %f seconds: %s',
                             self.sleeptime, reason)
                self._reconnecting = True
                connection.ioloop.call_later(self.sleeptime, self.reconnect)

    def reconnect(self):
        r"""Try to re-establish a connection and resume a new IO loop."""
        self.debug('')
        # This is the old connection IOLoop instance, stop its ioloop
        # with self.rmq_lock:
        self.connection.ioloop.stop()
        if not self._closing:
            # self.run_thread()
            # Create a new connection
            self.connect()
            # There is now a new connection, needs a new ioloop to run
            self._reconnecting = False
            self.connection.ioloop.start()

    # CHANNEL
    @property
    def channel_open(self):
        r"""bool: True if connection ready for messages, False otherwise."""
        with self.rmq_lock:
            if self.channel is None or self.connection is None:
                return False
            if self.channel.is_open:
                if not self.channel.is_closing:
                    return True
            return False  # pragma: debug

    @property
    def channel_stable(self):
        r"""bool: True if the connection ready for messages and not about to
        close. False otherwise."""
        with self.rmq_lock:
            return (self.channel_open and (not self._closing)
                    and (not self._opening))
        
    def open_channel(self):
        r"""Open a RabbitMQ channel."""
        self.debug('::Creating a new channel')
        self.connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        r"""Actions to perform after a channel is opened. Add the channel
        close callback and setup the exchange."""
        self.debug('::Channel opened')
        self.channel = channel
        channel.add_on_close_callback(self.on_channel_closed)
        self.setup_exchange(self.exchange)

    def on_channel_closed(self, channel, reason):
        r"""Actions to perform when the channel is closed. Close the
        connection."""
        with self.rmq_lock:
            self.debug('::channel %i was closed: %s', channel, reason)
            if not (channel.connection.is_closing or channel.connection.is_closed):
                channel.connection.close()
            self.channel = None
            # if self.connection is not None:
            #     self.connection.close()

    # EXCHANGE
    def setup_exchange(self, exchange_name):
        r"""Setup the exchange."""
        self.debug('::Declaring exchange %s', exchange_name)
        self.channel.exchange_declare(callback=self.on_exchange_declareok,
                                      exchange=exchange_name,
                                      auto_delete=True)

    def on_exchange_declareok(self, unused_frame):
        r"""Actions to perform once an exchange is succesfully declared.
        Set up the queue."""
        self.debug('::Exchange declared')
        self.setup_queue()

    # QUEUE
    def setup_queue(self):
        r"""Set up the message queue."""
        self.debug('::Declaring queue %s', self.queue)
        if self.direction == 'recv' and not self.queue:
            exclusive = False  # True
        else:
            exclusive = False
        if self.queue.startswith('amq.'):
            passive = True
        else:
            passive = False
        self.channel.queue_declare(queue=self.queue,
                                   callback=self.on_queue_declareok,
                                   exclusive=exclusive,
                                   # , auto_delete=True,
                                   passive=passive)

    def on_queue_declareok(self, method_frame):
        r"""Actions to perform once the queue is succesfully declared. Bind
        the queue."""
        self.debug('::Binding')
        with self.rmq_lock:
            if not self.queue:
                self.address += method_frame.method.queue
        self.channel.queue_bind(callback=self.on_bindok,
                                exchange=self.exchange,
                                # routing_key=self.routing_key,
                                queue=self.queue)
        
    def on_bindok(self, unused_frame):
        r"""Actions to perform once the queue is succesfully bound. Start
        consuming messages."""
        self.debug('::Queue bound')
        self.channel.basic_qos(prefetch_count=1)
        self.channel.add_on_cancel_callback(self.on_cancelok)
        if self.direction == 'recv':
            kwargs = dict(on_message_callback=self.on_message,
                          queue=self.queue)
            self.consumer_tag = self.channel.basic_consume(**kwargs)
        with self.rmq_lock:
            self._opening = False

    # GENERAL
    def on_cancelok(self, unused_frame):
        r"""Actions to perform after succesfully cancelling consumption. Closes
        the channel."""
        self.debug('::on_cancelok()')
        with self.rmq_lock:
            self.close_queue()
            self.close_channel()

    def close_connection(self):
        r"""Stop the ioloop and close the connection."""
        if self.connection:  # pragma: debug
            self.connection.ioloop.stop()
        super(RMQAsyncComm, self).close_connection()

    def force_close(self):  # pragma: debug
        r"""Force stop by removing the queue and stopping the IO loop."""
        with self.rmq_lock:
            self.close_queue()
            self.close_connection()
            self.channel = None
            self.connection = None
            self._closing = False

    def purge(self):
        r"""Remove all messages from the associated queue."""
        with self.rmq_lock:
            self._buffered_messages = []
            if not self.channel_stable:  # pragma: debug
                return
            super(RMQAsyncComm, self).purge()
