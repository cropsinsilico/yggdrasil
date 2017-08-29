"""This driver handles RabbitMQ connections."""
import os
from logging import debug, info
import logging
import pika
from IODriver import IODriver, maxMsgSize
from pika.connection import LOGGER as pika_logger


class LoggerFilterNormalCloseIsFine(logging.Filter):
    def filter(self, record):
        return not record.getMessage().endswith('(200): Normal shutdown')
pika_logger.addFilter(LoggerFilterNormalCloseIsFine())


class RMQConnection(IODriver):
    r"""Class for handling RabbitMQ communications.

    Args:
        name (str): The name of the local message queue that the driver should
            connect to. 
        suffix (str): Suffix added to name to create the environment variable
            where the message queue key is stored.
        args (str): The name of the RabbitMQ message queue that the driver 
            should connect to.
        \*\*kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    Attributes (in addition to the parent class's):
        args (str): The name of the RabbitMQ message queue that the driver 
            should connect to.
        connection (:class:`pika.Connection`): RabbitMQ connection.
        user (str): RabbitMQ server username. (From environment variable 
            'PSI_MSG_USER'.)
        server (str): RabbitMQ server. (From environment variable
            'PSI_MSG_SERVER'.)
        passwd (str): RabbitMQ server password. (From environment variable
            'PSI_MSG_PW'.)
        queue (object): RabbitMQ queue.
        channel (object): RabbitMQ channel.

    """
    def __init__(self, name, suffix, args=None, **kwargs):
        super(RMQConnection, self).__init__(name, suffix, **kwargs)
        self.debug()
        if args is None:
            args = name
        # Make the RMQ connection
        self.args = args
        self.connection = None
        self.user = os.environ['PSI_MSG_USER']
        self.server = os.environ['PSI_MSG_SERVER']
        self.passwd = os.environ['PSI_MSG_PW']
        self.queue = None
        self.channel = None
        self._closing = False
        self.connect()

    def __del__(self):
        self.debug("::__del__:")
        try:
            self.debug('~')
            if self.connection is not None:
                self.connection.close()
            self.connection = None
        except:
            self.debug("::__del__(): exception")

    def connect(self):
        r"""Establish the connection."""
        creds = pika.PlainCredentials(self.user, self.passwd)
        self._opening = True
        self.connection = pika.SelectConnection(
            pika.ConnectionParameters(host=self.server,\
                credentials=creds, heartbeat_interval=120, \
                connection_attempts=3),
            on_open_callback=self.on_connection_open,
            on_open_error_callback=self.on_connection_open_error,
            stop_ioloop_on_close=False)

    def start(self):
        r"""Start the driver. Waiting for connection."""
        super(RMQConnection, self).start()
        tries = 10
        while self._opening and tries > 0:
            self.sleep()
            tries -= 1
        if self._opening:
            raise RuntimeError("Connection never finished opening.")

    def run(self):
        r"""Run the driver. Connect to the connection and begin the IO loop."""
        self.debug("::run")
        self.connection.connect()
        self.connection.ioloop.start()
        self.debug("::run returns")

    def terminate(self):
        r"""Terminate the driver by closing the RabbitMQ connection."""
        self.debug('::terminate: Closing connection')
        super(RMQConnection, self).terminate()
        self._closing = True
        if self.connection is not None:
            self.connection.close()
        self.debug('::terminate returns')

    def rmq_send(self, data):
        r"""Send a message smaller than maxMsgSize to the RMQ queue.

        Args:
            str: The message to be sent.

        """
        self.debug(".send %d", len(data))
        if not self.channel:
            self.debug(".send %d  NO CHANNEL", len(data))
            return False
        try:
            # self._channel.confirm_delivery(self.publish_message) 
            self.channel.basic_publish(
                exchange=os.environ['PSI_NAMESPACE'],
                routing_key=self.args, body=data, mandatory=True)
        except Exception as e:
            self.warn(".send %d : exception %s: %s",
                      len(data), type(e), e)
        return True

    def rmq_send_nolimit(self, data):
        r"""Send a message smaller than maxMsgSize to the RMQ queue.

        Args:
            str: The message to be sent.

        """
        self.debug(".send_nolimit %d", len(data))
        if not self.channel:
            self.debug(".send_nolimit %d  NO CHANNEL", len(data))
            return False
        prev = 0
        ret = self.rmq_send("%ld" % len(data))
        if not ret:
            return ret
        while prev < len(data):
            next = min(prev+maxMsgSize, len(data))
            ret = self.rmq_send(data[prev:next])
            prev = next
            if not ret:
                break
        return ret

    def on_connection_open(self, unused_connection):
        r"""Actions that must be taken when the connection is opened.
        Add the close connection callback and open the RabbitMQ channel."""
        self.debug('::Connection opened')
        self.add_on_connection_close_callback()
        self.open_channel()

    def on_connection_open_error(self, unused_connection):
        r"""Actions that must be taken when the connection fails to open."""
        self.debug('::Connection could not be opened')
        self.terminate()
        raise Exception('Could not connect.')

    # TODO: Is this really necessary?
    def add_on_connection_close_callback(self):
        r"""Add the close connection callback."""
        self.debug('::Adding connection close callback')
        self.connection.add_on_close_callback(self.on_connection_closed)

    def on_connection_closed(self, connection, reply_code, reply_text):
        r"""Actions that must be taken when the connection is closed. Set the
        channel to None. If the connection is meant to be closing, stop the
        IO loop. Otherwise, wait 5 seconds and try to reconnect."""
        self.debug('::on_connection_closed code %d %s', reply_code, reply_text)
        self.channel = None
        if self._closing or reply_code == 200:
            self.connection.ioloop.stop()
        else:
            warning('RMQConnection(%s): Connection closed, reopening in 5 seconds: (%s) %s',\
                    self.name, reply_code, reply_text)
            self.connection.add_timeout(5, self.reconnect)

    def reconnect(self):
        r"""Try to re-establish a connection and resume a new IO loop."""
        self.debug('::reconnect()')
        # This is the old connection IOLoop instance, stop its ioloop
        self.connection.ioloop.stop()
        if not self._closing:
            # Create a new connection
            # self.connection = self.connect()
            self.connect()
            # There is now a new connection, needs a new ioloop to run
            self.connection.ioloop.start()

    def open_channel(self):
        r"""Open a RabbitMQ channel."""
        self.debug('::Creating a new channel')
        self.connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        r"""Actions to perform after a channel is opened. Add the channel
        close callback and setup the exchange."""
        self.debug('::Channel opened')
        self.channel = channel
        self.add_on_channel_close_callback()
        self.setup_exchange(os.environ['PSI_NAMESPACE'])

    def add_on_channel_close_callback(self):
        r"""Add the channel close callback."""
        self.debug('::Adding channel close callback')
        self.channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reply_code, reply_text):
        r"""Actions to perform when the channel is closed. Close the
        connection."""
        self.debug('::channel %i was closed: (%s) %s', channel, reply_code, reply_text)
        self.connection.close()

    def setup_exchange(self, exchange_name):
        r"""Setup the exchange."""
        self.debug('::Declaring exchange %s', exchange_name)
        self.channel.exchange_declare(self.on_exchange_declareok,\
                                      exchange=exchange_name, auto_delete=True)

    def on_exchange_declareok(self, unused_frame):
        r"""Actions to perform once an exchange is succesfully declared.
        Set up the queue."""
        self.debug('::Exchange declared')
        self.setup_queue(self.args)

    def setup_queue(self, queue_name):
        r"""Set up the message queue."""
        self.debug('::Declaring queue %s', queue_name)
        self.channel.queue_declare(self.on_queue_declareok, queue_name,
                                   auto_delete=True)

    def on_queue_declareok(self, method_frame):
        r"""Actions to perform once the queue is succesfully declared. Bind
        the queue."""
        self.debug('::Binding')
        self.queue = method_frame.method.queue
        self.channel.queue_bind(self.on_bindok, \
                                exchange=os.environ['PSI_NAMESPACE'], \
                                queue=self.args, routing_key=self.args)
        
    def on_bindok(self, unused_frame):
        r"""Actions to perform once the queue is succesfully bound. Start
        consuming messages."""
        self.debug('::Queue bound')
        self.start_consuming()
        self._opening = False

    def start_consuming(self):
        r"""Start publishing messages from the local queue."""
        self.debug('::start_consuming')
        self.add_on_cancel_callback()
        
    def add_on_cancel_callback(self):
        r"""Add the callabck for when consumption is cancelled."""
        self.debug('::Adding consumer cancellation callback')
        self.channel.add_on_cancel_callback(self.on_consumer_cancelled)
        
    def on_consumer_cancelled(self, method_frame):
        r"""Actions to perform when consumption is cancelled."""
        self.debug('::Consumer was cancelled remotely, shutting down: %r',
                   method_frame)
        self.info("consumer cancelled")
        self._closing = True
        if self.channel:
           self.channel.close()
        
