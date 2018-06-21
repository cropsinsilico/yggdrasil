from cis_interface.communication import CommBase, AsyncComm
from cis_interface.config import cis_cfg
import logging
try:
    import pika
    _rmq_installed = True
except ImportError:
    logging.warning("Could not import pika. " +
                    "RabbitMQ support will be disabled.")
    pika = None
    _rmq_installed = False
from cis_interface.schema import register_component


_rmq_param_sep = '_RMQPARAM_'


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
    if not _rmq_installed:
        return False
    if url is not None:
        parameters = pika.URLParameters(url)
    else:
        username = kwargs.get('username', cis_cfg.get('rmq', 'user', 'guest'))
        password = kwargs.get('password', cis_cfg.get('rmq', 'password', 'guest'))
        host = kwargs.get('host', cis_cfg.get('rmq', 'host', 'localhost'))
        port = kwargs.get('port', cis_cfg.get('rmq', 'port', '5672'))
        vhost = kwargs.get('vhost', cis_cfg.get('rmq', 'vhost', '/'))
        credentials = pika.PlainCredentials(username, password)
        parameters = pika.ConnectionParameters(host=host, port=int(port),
                                               virtual_host=vhost,
                                               credentials=credentials)
    # Try to establish connection
    try:
        connection = pika.BlockingConnection(parameters)
        if not connection.is_open:  # pragma: debug
            return False
        connection.close()
    except BaseException:  # pragma: debug
        return False
    return True


_rmq_server_running = check_rmq_server()


class RMQServer(CommBase.CommServer):
    r"""RMQ server object for cleaning up server connections."""

    def terminate(self, *args, **kwargs):
        CommBase.unregister_comm('RMQComm', self.srv_address)
        super(RMQServer, self).terminate(*args, **kwargs)


@register_component
class RMQComm(AsyncComm.AsyncComm):
    r"""Class for handling basic RabbitMQ communications.

    Attributes:
        connection (:class:`pika.Connection`): RabbitMQ connection.
        channel (:class:`pika.Channel`): RabbitMQ channel.

    Raises:
        RuntimeError: If a connection cannot be established.

    """

    _commtype = 'rmq'
    
    def _init_before_open(self, **kwargs):
        r"""Set null connection and channel."""
        self.connection = None
        self.channel = None
        self._is_open = False
        self._bound = False
        # Check that connection is possible
        if not check_rmq_server(self.url):  # pragma: debug
            raise RuntimeError("Could not connect to RabbitMQ server.")
        self._server_class = RMQServer
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
                'host' in section 'rmq' if it exists and 'localhost' if it
                does not. If 'localhost', the output of socket.gethostname()
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
            if user is None:
                user = cis_cfg.get('rmq', 'user', 'guest')
            if password is None:
                password = cis_cfg.get('rmq', 'password', 'guest')
            if host is None:
                host = cis_cfg.get('rmq', 'host', 'localhost')
            # if host == 'localhost':
            #     host = socket.gethostname()
            if virtual_host is None:
                virtual_host = cis_cfg.get('rmq', 'vhost', '/')
            if virtual_host == '/':
                virtual_host = '%2f'
            if port is None:
                port = cis_cfg.get('rmq', 'port', '5672')
            if exchange is None:
                exchange = cis_cfg.get('rmq', 'namespace', '')
            url = 'amqp://%s:%s@%s:%s/%s' % (
                user, password, host, port, virtual_host)
            kwargs['address'] = _rmq_param_sep.join([url, exchange, queue])
        return args, kwargs

    @classmethod
    def is_installed(cls):
        r"""bool: Is the comm installed."""
        return _rmq_server_running

    @classmethod
    def underlying_comm_class(self):
        r"""str: Name of underlying communication class."""
        return 'RMQComm'

    def opp_comm_kwargs(self):
        r"""Get keyword arguments to initialize communication with opposite
        comm object.

        Returns:
            dict: Keyword arguments for opposite comm object.

        """
        kwargs = super(RMQComm, self).opp_comm_kwargs()
        return kwargs

    def bind(self):
        r"""Declare queue to get random new queue."""
        if self.is_open or self._bound:
            return
        self._bound = True
        parameters = pika.URLParameters(self.url)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=self.exchange,
                                      auto_delete=True)
        if self.direction == 'recv' and not self.queue:
            exclusive = False  # True
        else:
            exclusive = False
        if self.queue.startswith('amq.'):
            passive = True
        else:
            passive = False
        res = self.channel.queue_declare(queue=self.queue,
                                         exclusive=exclusive,
                                         passive=passive,
                                         auto_delete=True)
        if not self.queue:
            self.address += res.method.queue
        self.channel.queue_bind(exchange=self.exchange,
                                # routing_key=self.routing_key,
                                queue=self.queue)
        self.register_comm(self.address, (self.connection, self.channel))
        super(RMQComm, self).bind()

    def _open_direct(self):
        r"""Open connection and bind/connect to queue as necessary."""
        super(RMQComm, self)._open_direct()
        if not self.is_open:
            self.bind()
            self._is_open = True
            self._bound = False

    def _close_direct(self, linger=False):
        r"""Close the connection.

        Args:
            linger (bool, optional): If True, drain messages before closing the
                comm. Defaults to False.

        """
        self._is_open = False
        self._bound = False
        if self.direction == 'recv':
            self.close_queue()
        self.close_channel()
        self.close_connection()
        if not self.is_client:
            self.unregister_comm(self.address)
        self.connection = None
        self.channel = None
        super(RMQComm, self)._close_direct(linger=linger)

    def close_queue(self):
        r"""Close the queue if the channel exists."""
        if self.channel and (not self.is_client):
            try:
                self.channel.queue_unbind(queue=self.queue,
                                          exchange=self.exchange)
                self.channel.queue_delete(queue=self.queue)
            except (pika.exceptions.ChannelClosed,
                    pika.exceptions.ConnectionClosed):  # pragma: debug
                pass
            except AttributeError:  # pragma: debug
                if self.channel is not None:
                    raise

    def close_channel(self):
        r"""Close the channel if it exists."""
        if self.channel:
            try:
                self.channel.close()
            except (pika.exceptions.ChannelClosed,
                    pika.exceptions.ConnectionClosed,
                    pika.exceptions.ChannelAlreadyClosing):  # pragma: debug
                pass
        self.channel = None

    def close_connection(self):
        r"""Close the connection."""
        if self.connection:
            try:
                self.connection.close()
            except (pika.exceptions.ChannelClosed,
                    pika.exceptions.ConnectionClosed,
                    pika.exceptions.ChannelAlreadyClosing):  # pragma: debug
                pass
            except AttributeError:  # pragma: debug
                pass
        self.connection = None

    @property
    def is_open_direct(self):
        r"""bool: True if the connection and channel are open."""
        # with self._closing_thread.lock:
        if self.channel is None or self.connection is None:
            return False
        if self.connection.is_open:
            if self.connection.is_closing:  # pragma: debug
                return False
        else:  # pragma: debug
            return False
        if self.channel.is_open:
            if self.channel.is_closing:  # pragma: debug
                return False
        else:  # pragma: debug
            return False
        return self._is_open

    def get_queue_result(self):
        r"""Get the fram from passive queue declare."""
        res = None
        if self.is_open_direct:
            try:
                res = self.channel.queue_declare(queue=self.queue,
                                                 auto_delete=True,
                                                 passive=True)
            except (pika.exceptions.ChannelClosed,
                    pika.exceptions.ConnectionClosed):  # pragma: debug
                self._close_direct()
        return res
        
    @property
    def n_msg_direct_recv(self):
        r"""int: Number of messages in the queue."""
        return self.n_msg_direct_send

    @property
    def n_msg_direct_send(self):
        r"""int: Number of messages in the queue."""
        out = 0
        # with self._closing_thread.lock:
        if self.is_open_direct:
            res = self.get_queue_result()
            if res is not None:
                out = res.method.message_count
        return out

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

    def _send_multipart_worker(self, msg, header, **kwargs):
        r"""Send multipart message to the worker comm identified.

        Args:
            msg (str): Message to be sent.
            header (dict): Message info including work comm address.

        Returns:
            bool: Success or failure of sending the message.

        """
        self.sched_task(0.0, super(RMQComm, self)._send_multipart_worker,
                        args=[msg, header], kwargs=kwargs, store_output=True)
        T = self.start_timeout()
        while (not T.is_out) and (self.sched_out is None):
            self.sleep()
        self.stop_timeout()
        out = self.sched_out
        self.sched_out = None
        # workcomm = self.get_work_comm(header)
        # args = [msg]
        # self.sched_task(self.sleeptime, workcomm._send_multipart,
        #                 args=args, kwargs=kwargs)
        # self.sched_task(1, self.remove_work_comm,
        #                 args=[header['id']], kwargs=dict(dont_close=True))
        # self.remove_work_comm(header['id'], dont_close=True)
        return out
    
    def _send_direct(self, msg, exchange=None, routing_key=None, **kwargs):
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
        out = self.channel.basic_publish(exchange, routing_key, msg, **kwargs)
        return out

    def _recv_direct(self):
        r"""Receive a message.

        Returns:
            tuple (bool, obj): Success or failure of receive and received
                message.

        """
        method_frame, props, msg = self.channel.basic_get(
            queue=self.queue, no_ack=False)
        if method_frame:
            self.channel.basic_ack(method_frame.delivery_tag)
        else:  # pragma: debug
            self.debug("No message")
            msg = self.empty_msg
        return (True, msg)

    def purge(self):
        r"""Remove all messages from the associated queue."""
        with self._closing_thread.lock:
            if self.channel:
                self.channel.queue_purge(queue=self.queue)
        super(RMQComm, self).purge()
