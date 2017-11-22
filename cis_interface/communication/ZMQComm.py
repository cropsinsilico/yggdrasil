import zmq
from cis_interface import backwards
from cis_interface.communication import CommBase


_registered_sockets = dict()


_socket_type_pairs = [('PUSH', 'PULL'),
                      ('PUB', 'SUB'),
                      ('REP', 'REQ'),
                      ('ROUTER', 'DEALER'),
                      ('PAIR', 'PAIR')]
_socket_send_types = [t[0] for t in _socket_type_pairs]
_socket_recv_types = [t[1] for t in _socket_type_pairs]
_socket_protocols = ['tcp', 'inproc', 'ipc', 'udp', 'pgm', 'epgm']
_flag_zmq_filter = backwards.unicode2bytes('_ZMQFILTER_')


def get_socket_type_mate(t_in):
    r"""Find the counterpart socket type.

    Args:
        t_in (str): Socket type.

    Returns:
        str: Counterpart socket type.

    Raises:
        ValueError: If t_in is not a recognized socket type.

    """
    if t_in in _socket_send_types:
        for t in _socket_type_pairs:
            if t[0] == t_in:
                return t[1]
    elif t_in in _socket_recv_types:
        for t in _socket_type_pairs:
            if t[1] == t_in:
                return t[0]
    else:
        raise ValueError('Could not locate socket type %s' % t_in)


class ZMQComm(CommBase.CommBase):
    r"""Class for handling I/O using ZeroMQ sockets.

    Args:
        name (str): The environment variable where the socket address is
            stored.
        context (zmq.Context, optional): ZeroMQ context that should be used.
            Defaults to None and the global context is used.
        socket_type (str, optional): The type of socket that should be created.
            Defaults to 'PAIR'. See zmq for all options.
        topic_filter (str, optional): Message filter to use when subscribing.
            This is only used for 'SUB' socket types. Defaults to '' which is
            all messages.
        dealer_identity (str, optional): Identity that should be used to route
            messages to a dealer socket. Defaults to '0'.
        dont_open (bool, optional): If True, the connection will not be opened.
            Defaults to False.
        **kwargs: Additional keyword arguments are passed to CommBase.

    Attributes:
        context (zmq.Context): ZeroMQ context that will be used.
        socket (zmq.Socket): ZeroMQ socket.
        socket_type_name (str): The type of socket that should be created.
        socket_type (int): ZeroMQ socket type.
        topic_filter (str): Message filter to use when subscribing.
        dealer_identity (str): Identity that should be used to route messages
            to a dealer socket.

    """
    def __init__(self, name, context=None, socket_type='PAIR', topic_filter='',
                 dealer_identity='0', dont_open=False, **kwargs):
        super(ZMQComm, self).__init__(name, dont_open=True, **kwargs)
        self.context = context or zmq.Context.instance()
        self.socket_type_name = socket_type
        self.socket_type = getattr(zmq, socket_type)
        self.socket = self.context.socket(self.socket_type)
        if socket_type in ['PULL', 'SUB', 'REQ', 'DEALER']:
            self.direction = 'recv'  # connect
        elif socket_type in ['PUSH', 'PUB', 'REP', 'ROUTER']:
            self.direction = 'send'  # bind
        self.topic_filter = backwards.unicode2bytes(topic_filter)
        self.dealer_identity = backwards.unicode2bytes(dealer_identity)
        self._openned = False
        self._bound = False
        self._recv_identities = set([])
        # Reserve port by binding
        if not dont_open:
            self.open()
        else:
            self.bind()

    @property
    def maxMsgSize(self):
        r"""int: Maximum size of a single message that should be sent."""
        # This is based on limit of 32bit int
        return 2**30

    @classmethod
    def comm_count(cls):
        r"""int: Number of sockets that have been opened on this process."""
        return len(_registered_sockets)

    @property
    def port(self):
        r"""str: Port that socket is connected to."""
        res = self.address.split(':')
        if len(res) == 3:
            out = int(res[-1])
        elif res[0] in ['inproc', 'ipc']:
            out = res[0]
        else:
            out = None
        return out

    @classmethod
    def new_comm_kwargs(cls, name, protocol='inproc', host='localhost',
                        port=None, **kwargs):
        r"""Initialize communication with new queue.

        Args:
            name (str): Name of new socket.
            protocol (str, optional): The protocol that should be used.
                Defaults to 'inproc'. See zmq for details.
            host (str, optional): The host that should be used. Invalid for
                'inproc' protocol. Defaults to 'localhost'.
            port (int, optional): The port used. Invalid for 'inproc' protocol.
                Defaults to None and a random port is choosen.
            **kwargs: Additional keywords arguments are returned as keyword
                arguments for the new comm.

        Returns:
            tuple(tuple, dict): Arguments and keyword arguments for new socket.

        """
        args = [name]
        if 'address' not in kwargs:
            if host == 'localhost':
                host = '127.0.0.1'
            if protocol in ['inproc', 'ipc']:
                suffix = cls._determine_suffix(**kwargs)
                address = "%s://%s" % (protocol, name + suffix)
            elif protocol not in _socket_protocols:
                raise ValueError("Unrecognized protocol: %s" % protocol)
            else:
                address = "%s://%s" % (protocol, host)
                if port is not None:
                    address += ":%d" % port
            kwargs['address'] = address
        return args, kwargs

    def opp_comm_kwargs(self):
        r"""Get keyword arguments to initialize communication with opposite
        comm object.

        Returns:
            dict: Keyword arguments for opposite comm object.

        """
        kwargs = super(ZMQComm, self).opp_comm_kwargs()
        kwargs['socket_type'] = get_socket_type_mate(self.socket_type_name)
        return kwargs

    def register_socket(self):
        r"""Register a socket."""
        global _registered_sockets
        key = '%s_%s' % (self.socket_type_name, self.address)
        _registered_sockets[key] = self.address

    def unregister_socket(self):
        r"""Unregister a socket."""
        global _registered_sockets
        key = '%s_%s' % (self.socket_type_name, self.address)
        if key in _registered_sockets:
            del _registered_sockets[key]
        
    def bind(self):
        r"""Bind to address, getting random port as necessary."""
        if self.is_open or self._bound:  # pragma: debug
            return
        self._bound = True
        if self.port is None:
            port = self.socket.bind_to_random_port(self.address)
            self.address += ":%d" % port
        else:
            if self.direction == 'send':
                try:
                    self.socket.bind(self.address)
                except zmq.ZMQError as e:
                    if (self.socket_type_name == 'PAIR') and (e.errno == 98):
                        self.error(("There is already a 'PAIR' socket sending " +
                                    "to %s. Maybe you meant to create a recv " +
                                    "PAIR?") % self.address)
                    raise e
            else:
                self._bound = False
        if self._bound:
            self.register_socket()

    def unbind(self):
        r"""Unbind from address."""
        if self._bound:
            self.socket.unbind(self.address)
            self.unregister_socket()

    def open(self):
        r"""Open connection by binding/connect to the specified socket."""
        super(ZMQComm, self).open()
        if not self.is_open:
            if self.direction == 'send':
                self.bind()
            elif self.direction == 'recv':
                # Bind then unbind to get port as necessary
                self.bind()
                self.unbind()
                # Connect and register
                if self.socket_type_name == 'DEALER':
                    self.socket.setsockopt(zmq.IDENTITY, self.dealer_identity)
                self.socket.connect(self.address)
                self.register_socket()
                if self.socket_type_name == 'SUB':
                    self.socket.setsockopt(zmq.SUBSCRIBE, self.topic_filter)
            self._openned = True

    def close(self):
        r"""Close connection."""
        if self.is_open or self._bound:
            self.socket.close()
            self._openned = False
            self.unregister_socket()
        super(ZMQComm, self).close()
            
    @property
    def is_open(self):
        r"""bool: True if the socket is open."""
        return (self._openned and not self.socket.closed)

    @property
    def n_msg(self):
        r"""int: 1 if there is 1 or more messages waiting. 0 otherwise."""
        if self.is_open:
            out = self.socket.poll(timeout=1, flags=zmq.POLLIN)  # |zmq.POLLOUT)
            if out == zmq.POLLIN:
                return 1
            # elif out == zmq.POLLOUT:
            #     return 1
            else:
                return 0
        return 0

    @property
    def get_work_comm_kwargs(self):
        r"""dict: Keyword arguments for an existing work comm."""
        out = super(ZMQComm, self).get_work_comm_kwargs
        out['socket_type'] = 'PAIR'
        return out

    @property
    def create_work_comm_kwargs(self):
        r"""dict: Keyword arguments for a new work comm."""
        out = super(ZMQComm, self).create_work_comm_kwargs
        out['socket_type'] = 'PAIR'
        return out
    
    def _send_multipart_worker(self, msg, header, **kwargs):
        r"""Send multipart message to the worker comm identified.

        Args:
            msg (str): Message to be sent.
            header (dict): Message info including work comm address.

        Returns:
            bool: Success or failure of sending the message.

        """
        workcomm = self.get_work_comm(header)
        args = [msg]
        self.sched_task(0, workcomm._send_multipart, args=args, kwargs=kwargs)
        return True

    def _send_multipart(self, msg, **kwargs):
        r"""Send a message larger than maxMsgSize in multiple parts.

        Args:
            msg (str): Message to send.
            **kwargs: Additional keyword arguments are passed to _send.

        Returns:
            bool: Success or failure of sending the message.

        """
        flag, _ = self._recv(timeout=self.timeout, flags=0)
        if not flag:  # pragma: debug
            return False
        flag = self._send(_, flags=0)
        flag = super(ZMQComm, self)._send_multipart(msg, **kwargs)
        return flag

    def _send(self, msg, topic='', identity='0', **kwargs):
        r"""Send a message.

        Args:
            msg (str, bytes): Message to be sent.
            topic (str, optional): Filter that should be sent with the
                message for 'PUB' sockets. Defaults to ''.
            identity (str, optional): Identify of identified worker that
                should be sent for 'ROUTER' sockets. Defaults to '0'.
            **kwargs: Additional keyword arguments are passed to socket send.

        Returns:
            bool: Success or failure of send.

        """
        if self.is_closed:  # pragma: debug
            self.error(".send(): Socket closed")
            return False
        topic = backwards.unicode2bytes(topic)
        identity = backwards.unicode2bytes(identity)
        if self.socket_type_name == 'PUB':
            total_msg = topic + _flag_zmq_filter + msg
        else:
            total_msg = msg
        # print('sending', self.address, self.is_open)
        try:
            kwargs.setdefault('flags', zmq.NOBLOCK)
            if self.socket_type_name == 'ROUTER':
                self.socket.send(identity, zmq.SNDMORE)
            self.socket.send(total_msg, **kwargs)
        except zmq.ZMQError:  # pragma: debug
            self.exception(".send(): Error")
            return False
        return True

    def _recv_multipart(self, *args, **kwargs):
        r"""Receive a message sent in multiple parts.

        Args:
            *args: All arguments are passed to parent _recv_multipart.
            **kwargs: All keyword arguments are passed to parent _recv_multipart.

        Returns:
            tuple (bool, str): The success or failure of receiving a message
                and the complete message received.

        """
        data = backwards.unicode2bytes('')
        flag = self._send(data)
        if not flag:  # pragma: debug
            return False, data
        flag, msg = self._recv(flags=0)
        if not flag:  # pragma: debug
            return False, data
        # kwargs['flags'] = 0
        # kwargs['timeout'] = self.timeout
        out = super(ZMQComm, self)._recv_multipart(*args, **kwargs)
        return out
    
    def _recv(self, timeout=None, **kwargs):
        r"""Receive a message from the ZMQ socket.

        Args:
            timeout (float, optional): Time in seconds to wait for a message.
                Defaults to self.recv_timeout.
            **kwargs: Additional keyword arguments are passed to socket send.

        Returns:
            tuple (bool, obj): Success or failure of receive and received
                message.

        """
        if self.is_closed:  # pragma: debug
            self.error(".recv(): Socket closed")
            return (False, None)
        if timeout is None:
            timeout = self.recv_timeout
        self.sleep()
        if timeout is not False:
            if self.is_closed:
                return (False, None)
            ret = self.socket.poll(timeout=1000.0 * timeout)
            if ret == 0:
                self.debug(".recv(): No messages waiting.")
                return (True, backwards.unicode2bytes(''))
            flags = zmq.NOBLOCK
        else:
            flags = 0
        # print('recving', self.address, self.is_open)
        try:
            if self.socket_type_name == 'ROUTER':
                identity = self.socket.recv(flags)
                self._recv_identities.add(identity)
            kwargs.setdefault('flags', flags)
            total_msg = self.socket.recv(**kwargs)
        except zmq.ZMQError:  # pragma: debug
            self.exception(".recv(): Error")
            return (False, None)
        if self.socket_type_name == 'SUB':
            topic, msg = total_msg.split(_flag_zmq_filter)
            assert(topic == self.topic_filter)
        else:
            msg = total_msg
        return (True, msg)

    def purge(self):
        r"""Purge all messages from the comm."""
        while self.n_msg > 0:
            self.socket.recv()
        super(ZMQComm, self).purge()
