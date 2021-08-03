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

    CLOSED = 0
    CONNECTION = 1
    CONNECTION_OPENED = 2
    CHANNEL_OPENED = 3
    EXCHANGE_DECLARED = 4
    QUEUE_DECLARED = 5
    QUEUE_BOUND = 6
    OPENED = 7
    
    def _init_before_open(self, **kwargs):
        r"""Initialize null variables and RMQ async thread."""
        self.times_connected = 0
        self.rmq_thread_count = 0
        self.rmq_thread = self.new_run_thread()
        self._opening_status = self.CLOSED
        self._reconnecting = multitasking.ProcessEvent()
        self._buffered_messages = []
        self._qres = None
        self._qres_lock = multitasking.RLock()
        self._qres_event = multitasking.Event()
        self._qres_event.set()
        super(RMQAsyncComm, self)._init_before_open(**kwargs)
        self._opening.stopped.add_callback(self._reconnecting.stop)
        self._closing.started.add_callback(self._qres_event.set)

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
        try:
            self.debug('')
            self.connect()
            self.connection.ioloop.start()
            self.debug("returning")
        finally:
            self._opening.stop()

    def start_run_thread(self):
        r"""Start the run thread and wait for it to finish."""
        with self.rmq_lock:
            if self.rmq_thread.was_started:
                return
            self.rmq_thread.start()
        # Wait for connection to be established
        self._opening.stopped.wait(self.timeout)
        # Check that connection was established
        if not self.rmq_thread.is_alive():  # pragma: debug
            self.force_close()
            raise Exception("Connection ioloop could not be established.")
        if not self.is_open:  # pragma: debug
            self.force_close()
            raise RuntimeError("Connection never finished opening ")

    def bind(self):
        r"""Declare queue to get random new queue."""
        if self._opening.has_started() or self._closing.has_started():
            return
        self._opening.start()
        self.start_run_thread()  # Start ioloop in a new thread
        # Register queue
        if not self.queue:  # pragma: debug
            self.error("Queue was not initialized.")
        self.register_comm(self.address, (self.connection, self.channel))
        super(RMQComm.RMQComm, self).bind()
    
    def _close(self, linger=False):
        r"""Close the connection.

        Args:
            linger (bool, optional): If True, drain messages before closing the
                comm. Defaults to False.

        """
        super(RMQAsyncComm, self)._close(linger=linger)
        if self.rmq_thread.is_alive():  # pragma: debug
            self.rmq_thread.join(self.timeout)
            if self.rmq_thread.is_alive():
                raise RuntimeError("Thread still running.")

    def close_on_thread(self):
        r"""Clean up pika objects based on opening callback reached."""
        with self.rmq_lock:
            if self._opening_status >= self.QUEUE_DECLARED:
                self.close_queue(
                    on_thread=True,
                    skip_unbind=(self._opening_status < self.QUEUE_BOUND))
            if self._opening_status >= self.CHANNEL_OPENED:
                self.close_channel(on_thread=True)
            else:
                self.close_connection(on_thread=True)
        
    def close_queue(self, on_thread=False, **kwargs):
        r"""Close the queue if the channel exists."""
        if on_thread:
            super(RMQAsyncComm, self).close_queue(**kwargs)

    def close_channel(self, on_thread=False, **kwargs):
        r"""Close the channel if it exists."""
        if on_thread:
            super(RMQAsyncComm, self).close_channel(**kwargs)
            return
        with self.rmq_lock:
            if self.direction == 'recv':
                if self.channel is not None:
                    self.channel.basic_cancel(callback=self.on_cancelok,
                                              consumer_tag=self.consumer_tag)
            else:
                if self.connection is not None:
                    self.connection.ioloop.add_callback_threadsafe(
                        lambda: self.close_channel(on_thread=True))
        self.debug("Waiting for channel to close in connection ioloop")
        self._closing.stopped.wait(self.timeout)
        if not self._closing.has_stopped():  # pragma: debug
            self.force_close()
        
    def close_connection(self, on_thread=False, **kwargs):
        r"""Close the connection."""
        if on_thread:
            if self.connection is not None:  # pragma: debug
                self.connection.ioloop.stop()
            super(RMQAsyncComm, self).close_connection(**kwargs)
            return
        if self.connection is not None:
            self.connection.ioloop.add_callback_threadsafe(
                lambda: self.close_connection(on_thread=True))
        
    @property
    def is_open(self):
        r"""bool: True if the connection and channel are open."""
        if self._reconnecting.is_running():
            return True
        return super(RMQAsyncComm, self).is_open
        
    def _set_qres(self, res):
        r"""Callback for getting message count."""
        self._qres = res
        self._qres_event.set()

    def get_queue_result(self):
        r"""Get the fram from passive queue declare."""
        res = None
        if self.is_open and (not self._reconnecting.is_running()):
            with self._qres_lock:
                if self._qres_event.is_set():
                    self._qres_event.clear()
                    self.channel.queue_declare(queue=self.queue,
                                               callback=self._set_qres,
                                               passive=True)
            self._qres_event.wait()
            res = self._qres
            assert(not self._closing.has_started())
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
        self._opening_status = self.CONNECTION
        self.times_connected += 1
        self.connection = pika.SelectConnection(
            pika.URLParameters(self.url),
            on_open_callback=self.on_connection_open,
            on_open_error_callback=self.on_connection_open_error)

    def on_connection_open(self, connection):
        r"""Actions that must be taken when the connection is opened.
        Add the close connection callback and open the RabbitMQ channel."""
        self._opening_status = self.CONNECTION_OPENED
        self.debug('::Connection opened')
        if self._opening.has_stopped():
            self.close_on_thread()
        else:
            connection.add_on_close_callback(self.on_connection_closed)
            self.open_channel()

    def on_connection_open_error(self, unused_connection, err):  # pragma: debug
        r"""Actions that must be taken when the connection fails to open."""
        self.debug('::Connection could not be opened')
        with self.rmq_lock:
            self.connection = None
            self._closing.start()
            self._closing.stop()
        raise Exception('Could not connect: %s.' % err)

    def on_connection_closed(self, connection, reason):
        r"""Actions that must be taken when the connection is closed. Set the
        channel to None. If the connection is meant to be closing, stop the
        IO loop. Otherwise, wait 5 seconds and try to reconnect."""
        with self.rmq_lock:
            self.debug('::on_connection_closed code %s', reason)
            if ((self._closing.is_running() or self._opening.is_running()
                 or (reason.reply_code == 200))):
                self.close_connection(on_thread=True)
                self._closing.stop()
                self._qres_event.set()
            else:
                self.warning('Connection closed, reopening in %f seconds: %s',
                             self.sleeptime, reason)
                self._reconnecting.started.clear()
                self._reconnecting.stopped.clear()
                self._reconnecting.start()  # stopped by re-opening
                connection.ioloop.call_later(self.sleeptime, self.reconnect)

    def reconnect(self):
        r"""Try to re-establish a connection and resume a new IO loop."""
        # Stop the old IOLoop, create a new connection and start a new IOLoop
        self.debug('')
        self._opening.stopped.clear()
        self.connection.ioloop.stop()
        if not self._closing.is_running():
            self.run_thread()

    # CHANNEL
    def open_channel(self):
        r"""Open a RabbitMQ channel."""
        self.debug('::Creating a new channel')
        self.connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        r"""Actions to perform after a channel is opened. Add the channel
        close callback and setup the exchange."""
        self._opening_status = self.CHANNEL_OPENED
        self.debug('::Channel opened')
        with self.rmq_lock:
            self.channel = channel
            channel.add_on_close_callback(self.on_channel_closed)
            if self._opening.has_stopped():
                self.close_on_thread()
            else:
                self.setup_exchange(self.exchange)

    def on_channel_closed(self, channel, reason):
        r"""Actions to perform when the channel is closed. Close the
        connection."""
        with self.rmq_lock:
            self.debug('::channel %i was closed: %s', channel, reason)
            if not (channel.connection.is_closing or channel.connection.is_closed):
                channel.connection.close()
            self.channel = None

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
        self._opening_status = self.EXCHANGE_DECLARED
        self.debug('::Exchange declared')
        if self._opening.has_stopped():
            self.close_on_thread()
        else:
            self.setup_queue()

    # QUEUE
    def setup_queue(self):
        r"""Set up the message queue."""
        self.debug('::Declaring queue %s', self.queue)
        self.channel.queue_declare(queue=self.queue,
                                   callback=self.on_queue_declareok,
                                   exclusive=False,
                                   passive=self.queue.startswith('amq.'))

    def on_queue_declareok(self, method_frame):
        r"""Actions to perform once the queue is succesfully declared. Bind
        the queue."""
        self._opening_status = self.QUEUE_DECLARED
        self.debug('::Binding')
        if self._opening.has_stopped():
            self.close_on_thread()
        else:
            with self.rmq_lock:
                if not self.queue:
                    self.address += method_frame.method.queue
            self.channel.queue_bind(callback=self.on_bindok,
                                    exchange=self.exchange,
                                    queue=self.queue)
        
    def on_bindok(self, unused_frame):
        r"""Actions to perform once the queue is succesfully bound. Start
        consuming messages."""
        self._opening_status = self.QUEUE_BOUND
        self.debug('::Queue bound')
        if self._opening.has_stopped():
            self.close_on_thread()
        else:
            self.channel.basic_qos(prefetch_count=1)
            self.channel.add_on_cancel_callback(self.on_cancelok)
            if self.direction == 'recv':
                kwargs = dict(on_message_callback=self.on_message,
                              queue=self.queue)
                self.consumer_tag = self.channel.basic_consume(**kwargs)
            self._opening.stop()
            self._opening_status = self.OPENED

    # GENERAL
    def on_cancelok(self, unused_frame):
        r"""Actions to perform after succesfully cancelling consumption. Closes
        the channel."""
        self.debug('::on_cancelok()')
        self.close_on_thread()

    def force_close(self):  # pragma: debug
        r"""Force stop by removing the queue and stopping the IO loop."""
        with self.rmq_lock:
            self.close_queue()
            self.close_connection()
            self.channel = None
            self.connection = None
            self._closing.stop()
