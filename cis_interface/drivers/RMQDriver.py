import pika
import socket
import requests
from pprint import pformat
from cis_interface.drivers.Driver import Driver
from cis_interface.drivers.IODriver import maxMsgSize
from cis_interface.config import cis_cfg
from cis_interface import backwards


class RMQDriver(Driver):
    r"""Class for handling basic RabbitMQ communications.

    Args:
        name (str): The name of the driver.
        queue (str, optional): Name of the queue that messages will be
            received from. If and empty string, the queue is exclusive to this
            connection. Defaults to ''.
        routing_key (str, optional): Routing key that should be used when the
            queue is bound. If None, the queue name is used. Defaults to None.
        user (str, optional): RabbitMQ server username. Defaults to config
            option 'user' in section 'rmq'.
        host (str, optional): RabbitMQ server host. Defaults to config option
            'host' in section 'rmq' if it exists and the output of
            socket.gethostname() if it does not.
        vhost (str, optional): RabbitMQ server virtual host. Defaults to
            config option 'vhost' in section 'rmq'.
        passwd (str, optional): RabbitMQ server password. Defaults to
            config option 'password' in section 'rmq'.
        exchange (str, optional): RabbitMQ exchange. Defaults to 'namespace'
            attribute which is set from the config option 'namespace' in the
            section 'rmq'.
        exclusive (bool, optional): If True, the queue that is created can
            only be used by this driver. Defaults to False. If a queue
            name is not provided, it is assumed exclusive.

    Attributes:
        user (str): RabbitMQ server username.
        passwd (str): RabbitMQ server password.
        host (str): RabbitMQ server host.
        vhost (str): RabbitMQ server virtual host.
        exchange (str): RabbitMQ exchange name.
        connection (:class:`pika.Connection`): RabbitMQ connection.
        channel (:class:`pika.Channel`): RabbitMQ channel.
        queue (str): Name of the queue that messages will be received
            from. If an empty string, the queue is exclusive to this
            connection.
        routing_key (str): Routing key that should be used when the queue is
            bound. If None, the queue name is used.
        times_connected (int): Number of times the connection has been
            established/re-established.

    """
    def __init__(self, name, queue='', routing_key=None, **kwargs):
        kwattr = ['user', 'passwd', 'host', 'vhost', 'exchange', 'exclusive']
        kwargs_attr = {k: kwargs.pop(k, None) for k in kwattr}
        super(RMQDriver, self).__init__(name, **kwargs)
        self.debug()
        self.user = cis_cfg.get('rmq', 'user')
        self.host = cis_cfg.get('rmq', 'host', socket.gethostname())
        self.vhost = cis_cfg.get('rmq', 'vhost')
        self.passwd = cis_cfg.get('rmq', 'password')
        self.exchange = self.namespace
        self.exclusive = False
        for k in kwattr:
            if kwargs_attr[k] is not None:
                setattr(self, k, kwargs_attr.pop(k))
            # if getattr(self, k) is None:  # pragma: debug
            #     raise Exception(("%s not provided and corresponding " +
            #                      "environment variable is not set.") % k)
        self.connection = None
        self.channel = None
        self.queue = queue
        self.routing_key = routing_key
        self.consumer_tag = ""
        self._opening = False
        self._closing = False
        self.times_connected = 0
        self.setDaemon(True)
        self._q_obj = None

    @property
    def is_valid(self):
        r"""bool: True if the channel is stable and the parent class is
        valid."""
        with self.lock:
            return (super(RMQDriver, self).is_valid and self.channel_stable)

    @property
    def channel_open(self):
        r"""bool: True if connection ready for messages, False otherwise."""
        with self.lock:
            if self.channel is None or self.connection is None:
                return False
            if self.channel.is_open:
                if not self.channel.is_closing:
                    return True
            return False

    @property
    def channel_stable(self):
        r"""bool: True if the connection ready for messages and not about to
        close. False otherwise."""
        with self.lock:
            return (self.channel_open and (not self._closing) and
                    (not self._opening))

    # DRIVER FUNCTIONALITY
    def start(self):
        r"""Start the driver. Waiting for connection."""
        self._opening = True
        super(RMQDriver, self).start()
        T = self.start_timeout()
        interval = 1  # timeout / 5
        while (not T.is_out) and (not self.channel_stable):
            self.sleep(interval)
        if not self.channel_stable:  # pragma: debug
            raise RuntimeError("Connection never finished opening " +
                               "(%f/%f timeout)." % (T.elapsed, T.max_time))
        self.stop_timeout()

    def run(self):
        r"""Run the driver. Connect to the connection and begin the IO loop."""
        super(RMQDriver, self).run()
        self.debug("::run")
        self.connect()
        self.connection.ioloop.start()
        self.debug("::run returns")

    def terminate(self):
        r"""Terminate the driver by closing the RabbitMQ connection."""
        if self._terminated:
            self.debug(':terminated() Driver already terminated.')
            return
        with self.lock:
            if self._closing:  # pragma: debug
                return  # Don't close more than once
        self.debug("::terminate")
        T = self.start_timeout()
        while self._opening and (not T.is_out):  # pragma: debug
            self.debug('Waiting for connection to open before terminating')
            # if self.connection is None:
            #     self.connection.add_timeout(self.terminate(), self.sleeptime)
            #     return
            # while self.connection is None:
            self.sleep()
        self.stop_timeout()
        self.debug('::terminate: Closing connection')
        self.stop_communication()
        # Only needed if ioloop is stopped prior to closing the connection?
        # (e.g. keyboard interupt)
        # if self.connection:
        #     self.connection.ioloop.start()
        super(RMQDriver, self).terminate()
        self.debug('::terminate returns')

    def on_model_exit(self):
        r"""Stop this driver if the model exits."""
        self.debug('::on_model_exit()')
        self.stop()
        super(RMQDriver, self).on_model_exit()

    def printStatus(self):
        r"""Print the driver status."""
        self.debug('::printStatus')
        super(RMQDriver, self).printStatus()
        qdata = self.get_message_stats()
        if qdata:
            qdata = pformat(qdata)
        self.display(": server info:\n%s", qdata)

    # RMQ PROPERTIES
    def get_message_stats(self):
        r"""Return message stats from the server."""
        hoststr = self.host
        # if self.host == '/':
        #     hoststr = '%2f'
        url = 'http://%s:%s/api/%s/%s/%s' % (
            hoststr, 15672, 'queues', '%2f', self.queue)
        res = requests.get(url, auth=(self.user, self.passwd))
        jdata = res.json()
        if isinstance(jdata, dict):
            qdata = jdata.get('message_stats', '')
        else:
            qdata = ''
        return qdata
        
    def on_nmsg_request(self, method_frame):
        r"""Actions to perform once the queue is declared for message count."""
        with self.lock:
            self._n_msg = 0
            if method_frame:
                self._n_msg = method_frame.method.message_count
                
    @property
    def n_rmq_msg(self):
        r"""int: Number of messages in the queue."""
        T = self.start_timeout()
        self._n_msg = None
        with self.lock:
            self.channel.queue_declare(self.on_nmsg_request,
                                       queue=self.queue,
                                       exclusive=self.exclusive,
                                       auto_delete=True,
                                       passive=True)
        # Wait for queue to be declared passively
        while (self._n_msg is None) and (not T.is_out):
            self.sleep()
        # Return result
        self.stop_timeout()
        n_msg = 0
        if self._n_msg is not None:
            n_msg = self._n_msg
        return n_msg
    
    @property
    def creds(self):
        r""":class:`pika.credentials.PlainCredentials`: Server credentials."""
        return pika.PlainCredentials(self.user, self.passwd)

    @property
    def connection_parameters(self):
        r""":class:`pika.connection.ConnectionParameters`: Connection
        parameters."""
        kws = dict(credentials=self.creds,
                   heartbeat_interval=120,
                   connection_attempts=3)
        if self.host is not None:
            kws['host'] = self.host
        return pika.ConnectionParameters(**kws)

    # CONNECTION
    def connect(self):
        r"""Establish the connection."""
        self.times_connected += 1
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

    def on_connection_open_error(self, unused_connection):  # pragma: debug
        r"""Actions that must be taken when the connection fails to open."""
        self.debug('::Connection could not be opened')
        self.terminate()
        raise Exception('Could not connect.')

    def on_connection_closed(self, connection, reply_code, reply_text):
        r"""Actions that must be taken when the connection is closed. Set the
        channel to None. If the connection is meant to be closing, stop the
        IO loop. Otherwise, wait 5 seconds and try to reconnect."""
        with self.lock:
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
        with self.lock:
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
        with self.lock:
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
        self.setup_queue(self.queue)

    # QUEUE
    def setup_queue(self, queue_name):
        r"""Set up the message queue."""
        self.debug('::Declaring queue %s', queue_name)
        if not queue_name:
            self.exclusive = True
        self.channel.queue_declare(self.on_queue_declareok,
                                   queue=queue_name,
                                   exclusive=self.exclusive,
                                   auto_delete=True)

    def on_queue_declareok(self, method_frame):
        r"""Actions to perform once the queue is succesfully declared. Bind
        the queue."""
        self.debug('::Binding')
        self._q_obj = method_frame.method
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
        with self.lock:
            self._opening = False
        self.start_communication()

    def purge_queue(self):
        r"""Remove all messages from the associated queue."""
        with self.lock:
            if not self.channel_stable:  # pragma: debug
                return
            if self.channel:
                self.channel.queue_purge(queue=self.queue)

    # GENERAL
    def remove_queue(self):
        r"""Unbind the queue from the exchange and delete the queue."""
        self.debug('::stop_communication: unbinding queue')
        if self.channel:
            # self.display('Unbinding queue')
            self.channel.queue_unbind(queue=self.queue,
                                      exchange=self.exchange)
            self.channel.queue_delete(queue=self.queue)
        
    def start_communication(self, **kwargs):
        r"""Start sending/receiving messages."""
        pass

    def stop_communication(self, remove_queue=True, cancel_consumer=False,
                           **kwargs):
        r"""Stop sending/receiving messages."""
        self.debug('::stop_communication')
        with self.lock:
            self._closing = True
            if self.channel_open:
                if cancel_consumer:
                    self.debug('::stop_communication: cancelling consumption')
                    # This cancels when basic_cancel dosn't work
                    # self.remove_queue()
                    # self.connection.ioloop.stop()
                    # self.channel = None
                    # self.connection = None
                    # self._closing = False
                    self.channel.basic_cancel(callback=self.on_cancelok,
                                              consumer_tag=self.consumer_tag)
                else:
                    if remove_queue:
                        self.remove_queue()
                    self.debug('::stop_communication: closing channel')
                    self.channel.close()
            else:
                self._closing = False
        T = self.start_timeout()
        while self._closing and (not T.is_out):
            self.debug('::stop_commmunication: waiting for connection to close')
            self.sleep()
        self.stop_timeout()

    def on_cancelok(self, unused_frame):
        r"""Actions to perform after succesfully cancelling consumption. Closes
        the channel."""
        self.debug('::on_cancelok()')
        with self.lock:
            if self.channel_open:
                self.remove_queue()
                self.channel.close()
                
    # UTILITIES
    def rmq_send(self, data):
        r"""Send a message smaller than maxMsgSize to the RMQ queue.

        Args:
            data (str): The message to be sent.

        Returns:
            bool: True if the message was sent succesfully. False otherwise.

        """
        backwards.assert_bytes(data)
        with self.lock:
            if not self.channel_stable:  # pragma: debug
                return False
            self.debug("::send %d", len(data))
            assert(len(data) <= maxMsgSize)
            if not self.channel:  # pragma: debug
                self.debug("::send %d  NO CHANNEL", len(data))
                return False
            try:
                self.channel.basic_publish(
                    exchange=self.exchange, routing_key=self.queue,
                    body=data, mandatory=True)
            except Exception as e:  # pragma: debug
                self.warn("::send %d : exception %s: %s",
                          len(data), type(e), e)
                return False
            return True

    def rmq_send_nolimit(self, data):
        r"""Send a message smaller than maxMsgSize to the RMQ queue.

        Args:
            data (str): The message to be sent.

        Returns:
            bool: True if the message was sent succesfully. False otherwise.

        """
        self.debug("::send_nolimit %d", len(data))
        prev = 0
        ret = self.rmq_send(backwards.unicode2bytes("%ld" % len(data)))
        if ret:
            while prev < len(data):
                next = min(prev + maxMsgSize, len(data))
                ret = self.rmq_send(data[prev:next])
                prev = next
                if not ret:  # pragma: debug
                    break
        return ret
