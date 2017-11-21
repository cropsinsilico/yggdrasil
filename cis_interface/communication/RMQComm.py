import pika
# import socket
from cis_interface import backwards
from cis_interface.communication import CommBase
from cis_interface.config import cis_cfg


_N_CONNECTIONS = 0
_registered_connections = {}
_rmq_param_sep = '_RMQPARAM_'


class RMQComm(CommBase.CommBase):
    r"""Class for handling basic RabbitMQ communications.

    Args:
        name (str): The environment variable where the comm address is stored.
        dont_open (bool, optional): If True, the connection will not be opened.
            Defaults to False.
        **kwargs: Additional keyword arguments are passed to CommBase.

    Attributes:
        connection (:class:`pika.Connection`): RabbitMQ connection.
        channel (:class:`pika.Channel`): RabbitMQ channel.

    """
    def __init__(self, name, dont_open=False, **kwargs):
        super(RMQComm, self).__init__(name, dont_open=True, **kwargs)
        self.connection = None
        self.channel = None
        self._is_open = False
        self._bound = False
        # Reserve port by binding
        if not dont_open:
            self.open()
        else:
            self.bind()

    @classmethod
    def comm_count(cls):
        r"""int: Number of connections that have been opened on this process."""
        return len(_registered_connections)

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
        if self.is_open:
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
        self.register_connection(res)

    def register_connection(self, res):
        r"""Add connection to list of registered connections.

        Args:
            res (obj): Object to register with connection address.

        """
        global _registered_connections
        if self.address not in _registered_connections:
            _registered_connections[self.address] = res

    def unregister_connection(self):
        r"""Remove connection from list of registered connections."""
        global _registered_connections
        if self.address not in _registered_connections:
            return
            # raise KeyError("Connection not registered.")
        del _registered_connections[self.address]
    
    def open(self):
        r"""Open connection and bind/connect to queue as necessary."""
        super(RMQComm, self).open()
        if not self.is_open:
            if not self._bound:
                self.bind()
            self._is_open = True
            self._bound = False

    def close(self):
        r"""Close connection."""
        self._is_open = False
        self._bound = False
        self.close_queue()
        self.close_channel()
        self.close_connection()
        self.unregister_connection()
        self.connection = None
        self.channel = None
        super(RMQComm, self).close()

    def close_queue(self):
        r"""Close the queue if the channel exists."""
        if self.channel:
            try:
                self.channel.queue_unbind(queue=self.queue,
                                          exchange=self.exchange)
                self.channel.queue_delete(queue=self.queue)
            except pika.exceptions.ChannelClosed:
                pass

    def close_channel(self):
        r"""Close the channel if it exists."""
        if self.channel:
            try:
                self.channel.close()
            except (pika.exceptions.ChannelClosed,
                    pika.exceptions.ChannelAlreadyClosing):
                pass
        self.channel = None

    def close_connection(self):
        r"""Close the connection."""
        if self.connection:
            self.connection.close()
        self.connection = None

    @property
    def is_open(self):
        r"""bool: True if the connection and channel are open."""
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
        else:
            return False
        return self._is_open
        
    @property
    def n_msg(self):
        r"""int: Number of messages in the queue."""
        out = 0
        if self.is_open:
            try:
                res = self.channel.queue_declare(queue=self.queue,
                                                 auto_delete=True,
                                                 passive=True)
                out = res.method.message_count
            except pika.exceptions.ChannelClosed:
                self.close()
                out = 0
        return out

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
        try:
            kwargs.setdefault('mandatory', True)
            out = self.channel.basic_publish(exchange, routing_key, msg, **kwargs)
        except pika.exceptions.AMQPError:
            self.exception(".send(): Error")
            raise
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
        try:
            method_frame, props, msg = self.channel.basic_get(
                queue=self.queue, no_ack=False)
            if method_frame:
                self.channel.basic_ack(method_frame.delivery_tag)
            else:
                self.debug(".recv(): No message")
                msg = backwards.unicode2bytes('')
        except pika.exceptions.AMQPError:
            self.exception(".recv(): Error")
            raise
        return (True, msg)

    def purge(self):
        r"""Remove all messages from the associated queue."""
        if self.channel:
            self.channel.queue_purge(queue=self.queue)
        super(RMQComm, self).purge()
