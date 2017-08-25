import os
import pika
from Driver import Driver


class RMQDriver(Driver):
    r"""Class for handling basic RabbitMQ communications.

    Args:
        name (str): The name of the driver.
        queue (str, optional): Name of the queue that messages will be 
            received from. If and empty string, the queue is exclusive to this
            connection. Defaults to ''.
        routing_key (str, optional): Routing key that should be used when the
            queue is bound. If None, the queue name is used. Defaults to None.
        user (str, optional): RabbitMQ server username. Defaults to environment
            variable 'PSI_MSG_USER' if it exists.
        server (str, optional): RabbitMQ server. Defaults to environment
            variable 'PSI_MSG_SERVER' if it exists.
        passwd (str, optional): RabbitMQ server password. Defaults to
            environment variable 'PSI_MSG_PW' if it exists.
        exchange (str, optional): RabbitMQ exchange. Defaults to 'namespace'
            attribute which is set from the environment variable
            'PSI_NAMESPACE'.

    Attributes (in addition to the parent class's):
        user (str): RabbitMQ server username.
        server (str): RabbitMQ server.
        passwd (str): RabbitMQ server password.
        exchange (str): RabbitMQ exchange name.
        connection (:class:`pika.Connection`): RabbitMQ connection.
        channel (:class:`pika.Channel`): RabbitMQ channel.
        queue (str): Name of the queue that messages will be received
            from. If an empty string, the queue is exclusive to this
            connection.
        routing_key (str): Routing key that should be used when the queue is
            bound. If None, the queue name is used.

    """
    def __init__(self, name, queue='', routing_key=None, **kwargs):
        super(RMQDriver, self).__init__(name, **kwargs)
        self.debug()
        self.user = os.environ.get('PSI_MSG_USER', None)
        self.server = os.environ.get('PSI_MSG_SERVER', None)
        self.passwd = os.environ.get('PSI_MSG_PW', None)
        self.exchange = self.namespace
        for k in ['user', 'server', 'passwd', 'exchange']:
            if k in kwargs:
                setattr(self, k, kwargs.pop(k))
            if getattr(self, k) is None:
                raise Exception("%s not provided and corresponding environment variable is not set." % k)
        self.connection = None
        self.channel = None
        self.queue = queue
        self.routing_key = routing_key
        self.consumer_tag = ""
        self._opening = False
        self._closing = False
        self.setDaemon(True)

    # DRIVER FUNCTIONALITY
    def start(self):
        r"""Start the driver. Waiting for connection."""
        self._opening = True
        super(RMQDriver, self).start()
        tries = 10
        while self._opening and tries > 0:
            self.sleep()
            tries -= 1
        if self._opening:
            raise RuntimeError("Connection never finished opening.")

    def run(self):
        r"""Run the driver. Connect to the connection and begin the IO loop."""
        super(RMQDriver, self).run()
        self.debug("::run")
        self.connect()
        self.connection.ioloop.start()
        self.debug("::run returns")

    def terminate(self):
        r"""Terminate the driver by closing the RabbitMQ connection."""
        if self._closing:
            return  # Don't close more than once
        super(RMQDriver, self).terminate()
        self.debug("::terminate")
        if self._opening:
            self.debug('Waiting for connection to open before terminating')
            while self.connection is None:
                self.sleep()
            self.connection.add_timeout(self.terminate(), self.sleeptime)
        self.debug('::terminate: Closing connection')
        self.stop_communication()
        # Only needed if ioloop is stopped prior to closing the connection?
        # (e.g. keyboard interupt)
        # if self.connection:
        #     self.connection.ioloop.start()
        self.debug('::terminate returns')

    # RMQ PROPERTIES
    @property
    def creds(self):
        r""":class:`pika.credentials.PlainCredentials`: Server credentials."""
        return pika.PlainCredentials(self.user, self.passwd)

    @property
    def connection_parameters(self):
        r""":class:`pika.connection.ConnectionParameters`: Connection 
        parameters."""
        return pika.ConnectionParameters(host=self.server,
                                         credentials=self.creds,
                                         heartbeat_interval=120,
                                         connection_attempts=3)

    # CONNECTION
    def connect(self):
        r"""Establish the connection."""
        self.connection = pika.SelectConnection(
            self.connection_parameters,
            on_open_callback=self.on_connection_open,
            on_open_error_callback=self.on_connection_open_error,
            stop_ioloop_on_close=False)

    def on_connection_open(self, unused_connection):
        r"""Actions that must be taken when the connection is opened.
        Add the close connection callback and open the RabbitMQ channel."""
        self.debug('::Connection opened')
        self.connection.add_on_close_callback(self.on_connection_closed)
        self.open_channel()

    def on_connection_open_error(self, unused_connection):
        r"""Actions that must be taken when the connection fails to open."""
        self.debug('::Connection could not be opened')
        self.terminate()
        raise Exception('Could not connect.')

    def on_connection_closed(self, connection, reply_code, reply_text):
        r"""Actions that must be taken when the connection is closed. Set the
        channel to None. If the connection is meant to be closing, stop the
        IO loop. Otherwise, wait 5 seconds and try to reconnect."""
        self.debug('::on_connection_closed code %d %s', reply_code, reply_text)
        self.channel = None
        if self._closing or reply_code == 200:
            self.connection.ioloop.stop()
        else:
            warning('RMQConnection(%s): Connection closed, reopening in 5 seconds: (%s) %s',
                    self.name, reply_code, reply_text)
            self.connection.add_timeout(5, self.reconnect)

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
        self.setup_queue(self.queue)

    # QUEUE
    def setup_queue(self, queue_name):
        r"""Set up the message queue."""
        self.debug('::Declaring queue %s', queue_name)
        if queue_name:
            exclusive = False
        else:
            exclusive = True
        self.channel.queue_declare(self.on_queue_declareok,
                                   queue=queue_name,
                                   exclusive=exclusive,
                                   auto_delete=True)

    def on_queue_declareok(self, method_frame):
        r"""Actions to perform once the queue is succesfully declared. Bind
        the queue."""
        self.debug('::Binding')
        self.queue = method_frame.method.queue
        if self.routing_key is None:
            self.routing_key = self.queue
        self.channel.queue_bind(self.on_bindok,
                                exchange=self.exchange,
                                queue=self.queue,
                                routing_key=self.routing_key)
        
    def on_bindok(self, unused_frame):
        r"""Actions to perform once the queue is succesfully bound. Start
        consuming messages."""
        self.debug('::Queue bound')
        self._opening = False
        self.start_communication()

    def purge_queue(self):
        r"""Remove all messages from the associated queue."""
        self.channel.queue_purge(queue=self.queue)

    # GENERAL
    def start_communication(self, **kwargs):
        r"""Start sending/receiving messages."""
        pass

    def stop_communication(self, **kwargs):
        r"""Stop sending/receiving messages."""
        self._closing = True
        if self.channel:
            self.channel.close()
