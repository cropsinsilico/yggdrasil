from yggdrasil import multitasking
from yggdrasil.communication import CommBase, NoMessages
from yggdrasil.config import ygg_cfg
import logging
logger = logging.getLogger(__name__)
try:
    import pika
    _rmq_installed = True
    _pika_version_maj = int(float(pika.__version__.split('.')[0]))
    if _pika_version_maj < 1:  # pragma: debug
        raise ImportError("pika version <1.0 no longer supported.")
except ImportError:
    logger.debug("Could not import pika. "
                 + "RabbitMQ support will be disabled.")
    pika = None
    _rmq_installed = False
    _pika_version_maj = 0


_rmq_param_sep = '_RMQPARAM_'
_localhost = '127.0.0.1'


def get_rmq_parameters(url=None, user=None, username=None,
                       password=None, host=None, virtual_host=None,
                       vhost=None, port=None, exchange=None, queue=''):
    r"""Get RabbitMQ connection parameters.

    Args:
        url (str, optional): Address of RMQ server that includes all the
            necessary information. If this is provided, the remaining arguments
            are ignored. Defaults to None and the connection parameters are
            taken from the other arguments.
        user (str, optional): RabbitMQ server username. Defaults to config
            option 'user' in section 'rmq' if it exists and 'guest' if it
            does not.
        username (str, optional): Alias for user.
        password (str, optional): RabbitMQ server password. Defaults to
            config option 'password' in section 'rmq' if it exists and
            'guest' if it does not.
        host (str, optional): RabbitMQ server host. Defaults to config option
            'host' in section 'rmq' if it exists and _localhost if it
            does not. If _localhost, the output of socket.gethostname()
            is used.
        virtual_host (str, optional): RabbitMQ server virtual host. Defaults
            to config option 'vhost' in section 'rmq' if it exists and '/'
            if it does not.
        vhost (str, optional): Alias for virtual_host.
        port (str, optional): Port on host to use. Defaults to config option
            'port' in section 'rmq' if it exists and '5672' if it does not.
        exchange (str, optional): RabbitMQ exchange. Defaults to config
            option 'namespace' in section 'rmq' if it exits and '' if it does
            not.
        queue (str, optional): Name of the queue that messages will be
            send to or received from. If an empty string, the queue will
            be a random string and exclusive to a receiving comm. Defaults
            to ''.

    Returns:
        tuple: The connection url, exchange, & queue.

    """
    if url is None:
        if user is None:
            user = username or ygg_cfg.get('rmq', 'user', 'guest')
        if password is None:
            password = ygg_cfg.get('rmq', 'password', 'guest')
        if host is None:
            host = ygg_cfg.get('rmq', 'host', _localhost)
        if virtual_host is None:
            virtual_host = vhost or ygg_cfg.get('rmq', 'vhost', '/')
        if virtual_host == '/':
            virtual_host = '%2f'
        if port is None:
            port = ygg_cfg.get('rmq', 'port', '5672')
        url = 'amqp://%s:%s@%s:%s/%s' % (
            user, password, host, port, virtual_host)
    if exchange is None:
        exchange = ygg_cfg.get('rmq', 'namespace', '')
    return url, exchange, queue


def check_rmq_server(url=None, **kwargs):
    r"""Check that connection to a RabbitMQ server is possible.

    Args:
        url (str, optional): Address of RMQ server that includes all the
            necessary information. If this is provided, the remaining arguments
            are ignored. Defaults to None and the connection parameters are
            taken from the other arguments.
        username (str, optional): RMQ server username. Defaults to config value.
        password (str, optional): RMQ server password. Defaults to config value.
        host (str, optional): RMQ hostname or IP Address to connect to. Defaults
            to config value.
        port (str, optional): RMQ server TCP port to connect to. Defaults to
            config value.
        vhost (str, optional): RMQ virtual host to use. Defaults to config value.

    Returns:
        bool: True if connection to RabbitMQ server is possible, False
            otherwise.

    """
    out = True
    if not _rmq_installed:
        return False
    if url is not None:
        parameters = pika.URLParameters(url)
    else:
        username = kwargs.get('username', ygg_cfg.get('rmq', 'user', 'guest'))
        password = kwargs.get('password', ygg_cfg.get('rmq', 'password', 'guest'))
        host = kwargs.get('host', ygg_cfg.get('rmq', 'host', _localhost))
        port = kwargs.get('port', ygg_cfg.get('rmq', 'port', '5672'))
        vhost = kwargs.get('vhost', ygg_cfg.get('rmq', 'vhost', '/'))
        credentials = pika.PlainCredentials(username, password)
        parameters = pika.ConnectionParameters(host=host, port=int(port),
                                               virtual_host=vhost,
                                               credentials=credentials)
    # Try to establish connection
    logging.getLogger("pika").propagate = False
    try:
        from yggdrasil import tools
        with tools.track_fds("pika test connection: "):
            connection = pika.BlockingConnection(parameters)
        if not connection.is_open:  # pragma: debug
            del connection
            raise BaseException("Connection was not opened.")
        connection.close()
        del connection
    except BaseException as e:  # pragma: debug
        print("Error when attempting to connect to the RabbitMQ server: "
              + str(e))
        out = False
    logging.getLogger("pika").propagate = True
    return out


class RMQServer(CommBase.CommServer):
    r"""RMQ server object for cleaning up server connections."""

    def __init__(self, *args, **kwargs):
        self.comm_cls = kwargs.get('comm_cls', RMQComm)
        super(RMQServer, self).__init__(*args, **kwargs)

    def terminate(self, *args, **kwargs):
        self.comm_cls.unregister_comm(self.srv_address)
        super(RMQServer, self).terminate(*args, **kwargs)


class RMQComm(CommBase.CommBase):
    r"""Class for handling basic RabbitMQ communications.

    Attributes:
        connection (:class:`pika.Connection`): RabbitMQ connection.
        channel (:class:`pika.Channel`): RabbitMQ channel.

    Raises:
        RuntimeError: If a connection cannot be established.

    Developer Notes:
        It is not advised that new language implement a RabbitMQ communication
        interface. Rather RMQ communication is included explicitly for
        connections between models that are not co-located on the same machine
        and are used by the |yggdrasil| framework connections on the Python side.

    """

    _commtype = 'rmq'
    _schema_subtype_description = ('RabbitMQ connection.')
    # Based on limit of 32bit int, this could be 2**30, but this is
    # too large for stack allocation in C so 2**20 will be used.
    _maxMsgSize = 2**20
    address_description = ("AMPQ queue address of the form "
                           "``<url>_RMQPARAM_<exchange>_RMQPARAM_<queue>`` "
                           "where ``url`` is the broker address (see explanation "
                           "`here <https://pika.readthedocs.io/en/stable/"
                           "examples/using_urlparameters.html>`_), "
                           "``exchange`` is the name of the exchange on the queue "
                           "that should be used, and ``queue`` is the name of "
                           "the queue.")
    _disconnect_attr = (CommBase.CommBase._disconnect_attr
                        + ['_opening', '_closing'])
    
    def _init_before_open(self, **kwargs):
        r"""Set null connection and channel."""
        if not hasattr(self, 'rmq_lock'):
            self.rmq_lock = multitasking.RLock()
        self.connection = None
        self.channel = None
        self._opening = multitasking.ProcessEvent()
        self._closing = multitasking.ProcessEvent()
        self._server_class = RMQServer
        self._server_kwargs = {'comm_cls': self.__class__}
        super(RMQComm, self)._init_before_open(**kwargs)

    @property
    def url(self):
        r"""str: AMQP server address."""
        return self.address.split(_rmq_param_sep)[0]

    @property
    def exchange(self):
        r"""str: AMQP exchange."""
        return self.address.split(_rmq_param_sep)[1]

    @property
    def queue(self):
        r"""str: AMQP queue."""
        return self.address.split(_rmq_param_sep)[2]

    @classmethod
    def new_comm_kwargs(cls, name, user=None, password=None, host=None,
                        virtual_host=None, port=None, exchange=None, queue='',
                        **kwargs):
        r"""Initialize communication with new connection.

        Args:
            name (str): Name of new connection.
            user (str, optional): RabbitMQ server username. Defaults to config
                option 'user' in section 'rmq' if it exists and 'guest' if it
                does not.
            password (str, optional): RabbitMQ server password. Defaults to
                config option 'password' in section 'rmq' if it exists and
                'guest' if it does not.
            host (str, optional): RabbitMQ server host. Defaults to config option
                'host' in section 'rmq' if it exists and _localhost if it
                does not. If _localhost, the output of socket.gethostname()
                is used.
            virtual_host (str, optional): RabbitMQ server virtual host. Defaults
                to config option 'vhost' in section 'rmq' if it exists and '/'
                if it does not.
            port (str, optional): Port on host to use. Defaults to config option
                'port' in section 'rmq' if it exists and '5672' if it does not.
            exchange (str, optional): RabbitMQ exchange. Defaults to config
                option 'namespace' in section 'rmq' if it exits and '' if it does
                not.
            queue (str, optional): Name of the queue that messages will be
                send to or received from. If an empty string, the queue will
                be a random string and exclusive to a receiving comm. Defaults
                to ''.
            **kwargs: Additional keywords arguments are returned as keyword
                arguments for the new comm.

        Returns:
            tuple(tuple, dict): Arguments and keyword arguments for new comm.
        
        """
        args = [name]
        if 'address' not in kwargs:
            (url, exchange, queue) = get_rmq_parameters(
                user=user, password=password, host=host,
                virtual_host=virtual_host, port=port, exchange=exchange,
                queue=queue)
            kwargs['address'] = _rmq_param_sep.join([url, exchange, queue])
        return args, kwargs

    def opp_comm_kwargs(self, for_yaml=False):
        r"""Get keyword arguments to initialize communication with opposite
        comm object.

        Args:
            for_yaml (bool, optional): If True, the returned dict will only
                contain values that can be specified in a YAML file. Defaults
                to False.

        Returns:
            dict: Keyword arguments for opposite comm object.

        """
        kwargs = super(RMQComm, self).opp_comm_kwargs(for_yaml=for_yaml)
        return kwargs

    def bind(self):
        r"""Declare queue to get random new queue."""
        if self._opening.has_started() or self._closing.has_started():
            return
        self._opening.start()
        with self.rmq_lock:
            if self.connection is None:
                parameters = pika.URLParameters(self.url)
                self.connection = pika.BlockingConnection(parameters)
                self.original_queue = self.queue
            self.channel = self.connection.channel()
            self.channel.exchange_declare(exchange=self.exchange,
                                          auto_delete=True)
            if self.direction == 'send':
                self.channel.confirm_delivery()
            res = self.channel.queue_declare(
                queue=self.queue, exclusive=False, auto_delete=True,
                passive=self.original_queue.startswith('amq.'))
            if not self.queue:
                self.address += res.method.queue
            self.channel.queue_bind(exchange=self.exchange,
                                    queue=self.queue)
            self.register_comm(self.address, (self.connection, self.channel))
            super(RMQComm, self).bind()
        self._opening.stop()

    def _close(self, linger=False):
        r"""Close the connection.

        Args:
            linger (bool, optional): If True, drain messages before closing the
                comm. Defaults to False.

        """
        if self._closing.has_started():  # pragma: debug
            return
        self._closing.start()
        if self.direction == 'recv':
            self.close_queue()
        self.close_channel()
        self.close_connection()
        if not self.is_client:
            self.unregister_comm(self.address)
        with self.rmq_lock:
            self.channel = None
            self.connection = None
        super(RMQComm, self)._close(linger=linger)
        self._closing.stop()

    def close_queue(self, skip_unbind=False):
        r"""Close the queue if the channel exists."""
        if self.direction != 'recv':
            return
        with self.rmq_lock:
            if self.channel and (not self.is_client):
                try:
                    if not skip_unbind:
                        self.channel.queue_unbind(queue=self.queue,
                                                  exchange=self.exchange)
                    self.channel.queue_delete(queue=self.queue)
                except (pika.exceptions.ChannelClosed,
                        pika.exceptions.ConnectionClosed,
                        pika.exceptions.ChannelWrongStateError,
                        pika.exceptions.ConnectionWrongStateError):  # pragma: debug
                    pass
                except AttributeError:  # pragma: debug
                    if self.channel is not None:
                        raise

    def close_channel(self):
        r"""Close the channel if it exists."""
        with self.rmq_lock:
            if self.channel is not None:
                self.debug('Closing the channel')
                try:
                    self.channel.close()
                except (pika.exceptions.ChannelWrongStateError,
                        pika.exceptions.StreamLostError):  # pragma: debug
                    pass

    def close_connection(self, *args, **kwargs):
        r"""Close the connection."""
        with self.rmq_lock:
            if self.connection is not None:
                self.debug('Closing connection')
                self.connection.close(*args, **kwargs)

    def atexit(self):  # pragma: debug
        r"""Close operations."""
        if self.direction == 'send':
            self.linger()
        super(RMQComm, self).atexit()
        
    @property
    def is_open(self):
        r"""bool: True if the connection and channel are open."""
        with self.rmq_lock:
            if self.channel is None or self.connection is None:
                return False
            if not self.connection.is_open:
                return False
            if not self.channel.is_open:
                return False
            return (self._opening.has_stopped()
                    and (not self._closing.has_started()))

    def get_queue_result(self):
        r"""Get the fram from passive queue declare."""
        with self.rmq_lock:
            res = None
            if self.is_open:
                try:
                    res = self.channel.queue_declare(queue=self.queue,
                                                     auto_delete=True,
                                                     passive=True)
                except pika.exceptions.ChannelClosedByBroker:  # pragma: debug
                    self._close()
                # except BlockingIOError:  # pragma: debug
                #     self.sleep()
                #     res = self.get_queue_result()
                # except (pika.exceptions.ChannelClosed,
                #         pika.exceptions.ConnectionClosed,
                #         pika.exceptions.ChannelWrongStateError,
                #         pika.exceptions.ConnectionWrongStateError,
                #         pika.exceptions.StreamLostError,
                #         AttributeError):  # pragma: debug
                #     self._close()
            return res
        
    @property
    def n_msg_recv(self):
        r"""int: Number of messages in the queue."""
        out = 0
        res = self.get_queue_result()
        if res is not None:
            out = res.method.message_count
        return out

    @property
    def n_msg_send(self):
        r"""int: Number of messages in the queue."""
        return 0

    @property
    def is_confirmed_send(self):
        r"""bool: True if all sent messages have been confirmed."""
        return True

    @property
    def is_confirmed_recv(self):
        r"""bool: True if all received messages have been confirmed."""
        return True

    @property
    def get_work_comm_kwargs(self):
        r"""dict: Keyword arguments for an existing work comm."""
        out = super(RMQComm, self).get_work_comm_kwargs
        out['exchange'] = self.exchange
        return out

    @property
    def create_work_comm_kwargs(self):
        r"""dict: Keyword arguments for a new work comm."""
        out = super(RMQComm, self).create_work_comm_kwargs
        out['exchange'] = self.exchange
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
        if exchange is None:
            exchange = self.exchange
        if routing_key is None:
            routing_key = self.queue
        kwargs.setdefault('mandatory', True)
        with self.rmq_lock:
            try:
                self.channel.basic_publish(exchange, routing_key, msg, **kwargs)
            except pika.exceptions.UnroutableError:  # pragma: debug
                return False
        return True

    def _recv(self):
        r"""Receive a message.

        Returns:
            tuple (bool, obj): Success or failure of receive and received
                message.

        """
        with self.rmq_lock:
            method_frame, props, msg = self.channel.basic_get(
                queue=self.queue, auto_ack=False)
            if method_frame:
                self.channel.basic_ack(method_frame.delivery_tag)
            else:  # pragma: debug
                raise NoMessages("No messages in connection.")
        return (True, msg)

    def purge(self):
        r"""Remove all messages from the associated queue."""
        if not self._closing.has_started():
            with self.rmq_lock:
                with self._closing_thread.lock:
                    if self.is_open:
                        self.channel.queue_purge(queue=self.queue)
        super(RMQComm, self).purge()
