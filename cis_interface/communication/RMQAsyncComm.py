import pika
from threading import Thread
from cis_interface.communication.RMQComm import RMQComm, _registered_connections


class RMQAsyncComm(RMQComm):
    r"""Class for handling asynchronous RabbitMQ communications.

    Args:
        name (str): The environment variable where the comm address is stored.
        dont_open (bool, optional): If True, the connection will not be opened.
            Defaults to False.
        **kwargs: Additional keyword arguments are passed to CommBase.

    Attributes:
        times_connected (int): Number of times that this connections has been
            established.

    """
    def __init__(self, name, **kwargs):
        self.times_connected = 0
        self._thread = None
        self._opening = False
        self._closing = False
        self._buffered_messages = []
        super(RMQAsyncComm, self).__init__(name, **kwargs)

    def run(self):
        r"""Run the driver. Connect to the connection and begin the IO loop."""
        self.debug("::run")
        self.connect()
        self.connection.ioloop.start()
        self.debug("::run returns")

    def bind(self):
        r"""Declare queue to get random new queue."""
        global _registered_connections
        if self.is_open:
            return
        self._bound = True
        self._opening = True
        self._thread = Thread(name=self.name, target=self.run)
        self._thread.start()
        # Wait for queue to be set so it can be registered
        T = self.start_timeout()
        while (not T.is_out) and (not self.queue):
            self.sleep(0.5)
        self.stop_timeout()
        if not self.queue:
            self.error("Queue was not initialized.")
        if self.address not in _registered_connections:
            _registered_connections[self.address] = self.queue  # self._thread
    
    def open(self):
        r"""Open connection and bind/connect to queue as necessary."""
        if not self.is_open:
            if not self._bound:
                self.bind()
            T = self.start_timeout()
            while (not T.is_out) and self._opening:
                self.sleep()
            self.stop_timeout()
            self._is_open = True
            self._bound = False

    def close(self):
        r"""Close connection."""
        if self._closing:
            return
        if not (self.is_open or self._bound):
            return
        global _registered_connections
        # Wait for connection to finish opening to close it
        T = self.start_timeout()
        while (not T.is_out) and self._opening:
            self.sleep()
        self.stop_timeout()
        # Close by cancelling consumption
        self._closing = True
        self._is_open = False
        self._bound = False
        if self.direction == 'recv':
            try:
                self.channel.basic_cancel(callback=self.on_cancelok,
                                          consumer_tag=self.consumer_tag)
            except pika.exceptions.ChannelClosed:  # pragma: debug
                self._closing = False
            if self.address not in _registered_connections:
                raise KeyError("Connection not registered.")
            del _registered_connections[self.address]
        else:
            self._closing = False
        # Wait for connection to finish closing & then force if it dosn't
        T = self.start_timeout()
        while (not T.is_out) and self._closing:
            self.sleep()
        self.stop_timeout()
        if self._closing:  # pragma: debug
            self.force_close()
        if self.connection is not None:
            try:
                self.connection.close()
            except pika.exceptions.ChannelClosed:
                pass
        self._thread.join()
        self._thread = None
        self.connection = None
        self.channel = None
        # Close workers
        super(RMQAsyncComm, self).close()

    @property
    def n_msg(self):
        r"""int: Number of messages in the queue."""
        out = 0
        if self.is_open:
            out = len(self._buffered_messages)
        return out

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
        out = super(RMQAsyncComm, self)._send(msg, exchange=exchange,
                                              routing_key=routing_key, **kwargs)
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
        while self.n_msg == 0 and self.is_open and (not Tout.is_out):
            self.sleep()
        self.stop_timeout()
        if self.is_closed:
            self.debug(".recv(): Connection closed.")
            return (False, None)
        if self.n_msg == 0:
            # self.debug(".recv(): No buffered messages.")
            return (True, '')
        return (True, self._buffered_messages.pop(0))

    def on_message(self, ch, method, props, body):
        r"""Buffer received messages."""
        self._buffered_messages.append(body)
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

    def on_connection_open(self, unused_connection):
        r"""Actions that must be taken when the connection is opened.
        Add the close connection callback and open the RabbitMQ channel."""
        self.debug('::Connection opened')
        self.connection.add_on_close_callback(self.on_connection_closed)
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
        self.debug('::on_connection_closed code %d %s', reply_code,
                   reply_text)
        if self._closing or reply_code == 200:
            self.connection.ioloop.stop()
            self.connection = None
            self._closing = False
        else:
            self.warn('Connection closed, reopening in %f seconds: (%s) %s',
                      self.sleeptime, reply_code, reply_text)
            self.connection.add_timeout(self.sleeptime, self.reconnect)

    def reconnect(self):
        r"""Try to re-establish a connection and resume a new IO loop."""
        self.debug('::reconnect()')
        # This is the old connection IOLoop instance, stop its ioloop
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
        if self.channel is None or self.connection is None:
            return False
        if self.channel.is_open:
            if not self.channel.is_closing:
                return True
        return False

    def open_channel(self):
        r"""Open a RabbitMQ channel."""
        self.debug('::Creating a new channel')
        self.connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        r"""Actions to perform after a channel is opened. Add the channel
        close callback and setup the exchange."""
        self.debug('::Channel opened')
        self.channel = channel
        self.channel.add_on_close_callback(self.on_channel_closed)
        self.setup_exchange(self.exchange)

    def on_channel_closed(self, channel, reply_code, reply_text):
        r"""Actions to perform when the channel is closed. Close the
        connection."""
        self.debug('::channel %i was closed: (%s) %s',
                   channel, reply_code, reply_text)
        self.channel = None
        self.connection.close()

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
        self._opening = False

    def purge_queue(self):
        r"""Remove all messages from the associated queue."""
        if self.channel:
            self.channel.queue_purge(queue=self.queue)

    # GENERAL
    def on_cancelok(self, unused_frame):
        r"""Actions to perform after succesfully cancelling consumption. Closes
        the channel."""
        self.debug('::on_cancelok()')
        if self.channel_open:
            self.remove_queue()
            self.channel.close()

    def remove_queue(self):
        r"""Unbind the queue from the exchange and delete the queue."""
        self.debug('::remove_queue: unbinding queue')
        if self.channel:
            self.channel.queue_unbind(queue=self.queue,
                                      exchange=self.exchange)
            self.channel.queue_delete(queue=self.queue)

    def force_close(self):  # pragma: debug
        r"""Force stop by removing the queue and stopping the IO loop."""
        if self.channel_open:
            self.remove_queue()
        if self.connection:
            self.connection.ioloop.stop()
        self.channel = None
        self.connection = None
        self._closing = False
