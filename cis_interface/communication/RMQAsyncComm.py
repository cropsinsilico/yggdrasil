import threading
from cis_interface import backwards, tools
from cis_interface.communication.RMQComm import RMQComm, _rmq_installed
if _rmq_installed:
    import pika
else:
    pika = False


class RMQAsyncComm(RMQComm):
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
        thread (tools.CisThread): Thread used to run IO loop.

    """
    def __init__(self, name, **kwargs):
        self.times_connected = 0
        self.thread = tools.CisThread(name=name, target=self.run_thread)
        self.lock = self.thread.lock
        self._opening = False
        self._closing = False
        self._close_called = False
        self._buffered_messages = []
        self._nmsg = 0
        self._nmsg_lock = threading.RLock()
        self._nmsg_event = threading.Event()
        self._nmsg_event.set()
        super(RMQAsyncComm, self).__init__(name, **kwargs)

    def run_thread(self):
        r"""Connect to the connection and begin the IO loop."""
        self.debug()
        self.connect()
        self.connection.ioloop.start()
        self.debug("returning")

    def bind(self):
        r"""Declare queue to get random new queue."""
        # Start ioloop in a new thread
        with self.lock:
            # Don't bind if already closing
            if self.is_open or self._close_called:  # pragma: debug
                return
            self._bound = True
            self._opening = True
            self.thread.start()
        # Wait for connection to be established
        T = self.start_timeout()
        # interval = 1  # timeout / 5
        while (not T.is_out) and (not self.channel_stable) and self.thread.isAlive():
            self.sleep()  # 0.5 # interval)
        self.stop_timeout()
        # Check that connection was established
        if not self.thread.isAlive():  # pragma: debug
            self._opening = False
            self.force_close()
            raise Exception("Connection ioloop could not be established.")
        if not self.channel_stable:  # pragma: debug
            self.force_close()
            raise RuntimeError("Connection never finished opening " +
                               "(%f/%f timeout)." % (T.elapsed, T.max_time))
        # Register queue
        if not self.queue:  # pragma: debug
            self.error("Queue was not initialized.")
        self.register_connection(self.queue)
    
    def open(self):
        r"""Open connection and bind/connect to queue as necessary."""
        super(RMQAsyncComm, self).open()
        T = self.start_timeout()
        while (not T.is_out) and self._opening:  # pragma: debug
            self.sleep()
        self.stop_timeout()

    def _close(self, linger=False):
        r"""Close the connection.

        Args:
            linger (bool, optional): If True, drain messages before closing the
                comm. Defaults to False.

        """
        with self.lock:
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
            with self.lock:
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
                    except pika.exceptions.ChannelClosed:  # pragma: debug
                        self._closing = False
            self.unregister_connection()
        # Wait for connection to finish closing & then force if it dosn't
        T = self.start_timeout(key=self.timeout_key + '_closing')
        while (not T.is_out) and self._closing:
            self.sleep()
        self.stop_timeout(key=self.timeout_key + '_closing')
        if self._closing:  # pragma: debug
            self.force_close()
        if self.thread.is_alive():
            self.thread.join(self.timeout)
        if self.thread.isAlive():  # pragma: debug
            raise RuntimeError("Thread still running.")
        # Close workers
        with self.lock:
            super(RMQAsyncComm, self)._close(linger=linger)

    def _set_nmsg(self, res):
        r"""Callback for getting message count."""
        self._nmsg = res.method.message_count
        self._nmsg_event.set()

    @property
    def n_msg_recv(self):
        r"""int: Number of messages in the queue."""
        out = 0
        with self.lock:
            out = len(self._buffered_messages)
        return out

    @property
    def n_msg_send(self):
        r"""int: Number of messages in the queue."""
        out = 0
        if self.is_open:
            with self._nmsg_lock:
                if self._nmsg_event.set():
                    self._nmsg_event.clear()
                    self.channel.queue_declare(self._set_nmsg,
                                               queue=self.queue,
                                               auto_delete=True, passive=True)
            self._nmsg_event.wait()
            out = self._nmsg
        return out

    # Access work comms with lock
    def get_work_comm(self, *args, **kwargs):
        r"""Alias for parent class that wraps method in Lock."""
        with self.lock:
            return super(RMQAsyncComm, self).get_work_comm(*args, **kwargs)

    def create_work_comm(self, *args, **kwargs):
        r"""Alias for parent class that wraps method in Lock."""
        with self.lock:
            return super(RMQAsyncComm, self).create_work_comm(*args, **kwargs)

    def add_work_comm(self, *args, **kwargs):
        r"""Alias for parent class that wraps method in Lock."""
        with self.lock:
            return super(RMQAsyncComm, self).add_work_comm(*args, **kwargs)

    def remove_work_comm(self, *args, **kwargs):
        r"""Alias for parent class that wraps method in Lock."""
        with self.lock:
            return super(RMQAsyncComm, self).remove_work_comm(*args, **kwargs)

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
        with self.lock:
            if self.is_closed:  # pragma: debug
                return False
            out = super(RMQAsyncComm, self)._send(msg, exchange=exchange,
                                                  routing_key=routing_key,
                                                  **kwargs)
        # Basic publish returns None for asynchronous connection
        if out is None:
            out = True
        return out

    def _recv(self, timeout=None):
        r"""Receive a message.

        Args:
            timeout (float, optional): Time in seconds to wait for a message.
                Defaults to self.recv_timeout.

        Returns:
            tuple (bool, obj): Success or failure of receive and received
                message.

        """
        if timeout is None:
            timeout = self.recv_timeout
        Tout = self.start_timeout(timeout)
        while ((self.n_msg_recv == 0) and self.is_open and
               (not Tout.is_out)):  # pragma: debug
            self.sleep()
        self.stop_timeout()
        if self.n_msg_recv != 0:
            with self.lock:
                out = (True, self._buffered_messages.pop(0))
            return out
        if self.is_closed:  # pragma: debug
            self.debug("Connection closed.")
            return (False, None)
        if self.n_msg_recv == 0:
            # self.debug(".recv(): No buffered messages.")
            out = (True, self.empty_msg)
        else:
            with self.lock:
                out = (True, self._buffered_messages.pop(0))
        return out

    def on_message(self, ch, method, props, body):
        r"""Buffer received messages."""
        if self.direction == 'send':  # pragma: debug
            raise Exception("Send comm received a message.")
        with self.lock:
            self._buffered_messages.append(backwards.unicode2bytes(body))
        ch.basic_ack(delivery_tag=method.delivery_tag)

    # CONNECTION
    def connect(self):
        r"""Establish the connection."""
        self.times_connected += 1
        parameters = pika.URLParameters(self.url)
        self.connection = pika.SelectConnection(
            parameters,
            on_open_callback=self.on_connection_open,
            on_open_error_callback=self.on_connection_open_error,
            stop_ioloop_on_close=False)

    def on_connection_open(self, connection):
        r"""Actions that must be taken when the connection is opened.
        Add the close connection callback and open the RabbitMQ channel."""
        self.debug('::Connection opened')
        connection.add_on_close_callback(self.on_connection_closed)
        self.open_channel()

    def on_connection_open_error(self, unused_connection):  # pragma: debug
        r"""Actions that must be taken when the connection fails to open."""
        self.debug('::Connection could not be opened')
        self.close()
        raise Exception('Could not connect.')

    def on_connection_closed(self, connection, reply_code, reply_text):
        r"""Actions that must be taken when the connection is closed. Set the
        channel to None. If the connection is meant to be closing, stop the
        IO loop. Otherwise, wait 5 seconds and try to reconnect."""
        with self.lock:
            self.debug('::on_connection_closed code %d %s', reply_code,
                       reply_text)
            if self._closing or reply_code == 200:
                connection.ioloop.stop()
                self.connection = None
                self._closing = False
            else:
                self.warn('Connection closed, reopening in %f seconds: (%s) %s',
                          self.sleeptime, reply_code, reply_text)
                connection.add_timeout(self.sleeptime, self.reconnect)

    def reconnect(self):
        r"""Try to re-establish a connection and resume a new IO loop."""
        self.debug()
        # This is the old connection IOLoop instance, stop its ioloop
        with self.lock:
            self.connection.ioloop.stop()
            if not self._closing:
                # Create a new connection
                self.connect()
                # There is now a new connection, needs a new ioloop to run
                self.connection.ioloop.start()

    # CHANNEL
    @property
    def channel_open(self):
        r"""bool: True if connection ready for messages, False otherwise."""
        with self.lock:
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
        with self.lock:
            return (self.channel_open and (not self._closing) and
                    (not self._opening))
        
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

    def on_channel_closed(self, channel, reply_code, reply_text):
        r"""Actions to perform when the channel is closed. Close the
        connection."""
        with self.lock:
            self.debug('::channel %i was closed: (%s) %s',
                       channel, reply_code, reply_text)
            channel.connection.close()
            self.channel = None
            # if self.connection is not None:
            #     self.connection.close()

    # EXCHANGE
    def setup_exchange(self, exchange_name):
        r"""Setup the exchange."""
        self.debug('::Declaring exchange %s', exchange_name)
        self.channel.exchange_declare(self.on_exchange_declareok,
                                      exchange=exchange_name, auto_delete=True)

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
        self.channel.queue_declare(self.on_queue_declareok,
                                   queue=self.queue,
                                   exclusive=exclusive,
                                   passive=passive,
                                   auto_delete=True)

    def on_queue_declareok(self, method_frame):
        r"""Actions to perform once the queue is succesfully declared. Bind
        the queue."""
        self.debug('::Binding')
        with self.lock:
            if not self.queue:
                self.address += method_frame.method.queue
        self.channel.queue_bind(self.on_bindok,
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
            self.consumer_tag = self.channel.basic_consume(self.on_message,
                                                           queue=self.queue)
        with self.lock:
            self._opening = False

    # GENERAL
    def on_cancelok(self, unused_frame):
        r"""Actions to perform after succesfully cancelling consumption. Closes
        the channel."""
        self.debug('::on_cancelok()')
        with self.lock:
            self.close_queue()
            self.close_channel()

    def close_connection(self):
        r"""Stop the ioloop and close the connection."""
        if self.connection:  # pragma: debug
            self.connection.ioloop.stop()
        super(RMQAsyncComm, self).close_connection()

    def force_close(self):  # pragma: debug
        r"""Force stop by removing the queue and stopping the IO loop."""
        with self.lock:
            self.close_queue()
            self.close_connection()
            self.channel = None
            self.connection = None
            self._closing = False

    def purge(self):
        r"""Remove all messages from the associated queue."""
        with self.lock:
            self._buffered_messages = []
            if not self.channel_stable:  # pragma: debug
                return
            super(RMQAsyncComm, self).purge()
