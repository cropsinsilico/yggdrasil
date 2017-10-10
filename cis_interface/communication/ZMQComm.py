import zmq
from cis_interface import backwards
from cis_interface.communication import CommBase


_N_SOCKETS = 0


_socket_type_pairs = [('PUSH', 'PULL'),
                      ('PUB', 'SUB'),
                      ('REP', 'REQ'),
                      ('DEALER', 'ROUTER'),
                      ('PAIR', 'PAIR')]
_socket_send_types = [t[0] for t in _socket_type_pairs]
_socket_recv_types = [t[1] for t in _socket_type_pairs]


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
        dont_open (bool, optional): If True, the connection will not be opened.
            Defaults to False.
        **kwargs: Additional keyword arguments are passed to CommBase.

    Attributes:
        context (zmq.Context): ZeroMQ context that will be used.
        socket (zmq.Socket): ZeroMQ socket.
        socket_type_name (str): The type of socket that should be created.
        socket_type (int): ZeroMQ socket type.

    """
    def __init__(self, name, context=None, socket_type='PAIR', dont_open=False,
                 **kwargs):
        super(ZMQComm, self).__init__(name, dont_open=True, **kwargs)
        self.context = context or zmq.Context.instance()
        self.socket_type_name = socket_type
        self.socket_type = getattr(zmq, socket_type)
        self.socket = self.context.socket(self.socket_type)
        if socket_type in ['PULL', 'SUB', 'REQ', 'ROUTER']:
            self.direction = 'recv'
        elif socket_type in ['PUSH', 'PUB', 'REP', 'DEALER']:
            self.direction = 'send'
        self._openned = False
        self._bound = False
        # Reserve port by binding
        if not dont_open:
            self.open()
        else:
            self.bind()

    @property
    def comm_count(self):
        r"""int: Number of sockets that have been opened on this process."""
        return _N_SOCKETS

    @property
    def port(self):
        r"""str: Port that socket is connected to."""
        res = self.address.split(':')
        if len(res) == 3:
            out = int(res[-1])
        elif res[0] == 'inproc':
            out = 'inproc'
        else:
            out = None
        return out

    @classmethod
    def new_comm_kwargs(cls, name, protocol='inproc', host='localhost', port=None,
                        **kwargs):
        r"""Initialize communication with new queue.

        Args:
            name (str): Name of new socket.
            protocol (str, optional): The protocol that should be used.
                Defaults to 'inproc'. See zmq for details.
            host (str, optional): The host that should be used. Invalid for
                'inproc' protocol. Defaults to 'localhost'.
            port (int, optional): The port used. Invalid for 'inproc' protocol.
                Defaults to None and a random port is choosen.
            **kwargs: Additional keywords arguments are passed to ZMQComm.

        Returns:
            dict: Keyword arguments for new socket.

        """
        args = [name]
        if 'address' not in kwargs:
            if host == 'localhost':
                host = '127.0.0.1'
            if protocol == 'inproc':
                address = "inproc://%s" % name
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

    def bind(self):
        r"""Bind to address, getting random port as necessary."""
        if self.port is None:
            port = self.socket.bind_to_random_port(self.address)
            self.address += ":%d" % port
        else:
            self.socket.bind(self.address)
        self._bound = True

    def open(self, reserve=False):
        r"""Open connection by binding/connect to the specified socket."""
        global _N_SOCKETS
        if not self.is_open:
            if self.direction == 'send':
                if not self._bound:
                    self.bind()
            elif self.direction == 'recv':
                if self.port is None:
                    self.bind()
                if self._bound:
                    self.socket.unbind(self.address)
                self.socket.connect(self.address)
            else:
                raise ValueError("Direction must be 'send' or 'recv'")
            self._openned = True
            _N_SOCKETS += 1

    def close(self):
        r"""Close connection."""
        if self.is_open:
            self.socket.close()
            
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
            return out
        return 0

    def _send(self, msg):
        r"""Send a message.

        Args:
            msg (str, bytes): Message to be sent.

        Returns:
            bool: Success or failure of send.

        """
        if self.socket.closed:
            self.error(".send(): Socket closed")
            return False
        try:
            msg_chunks = [_ for _ in self.chunk_message(msg)]
            self.socket.send_multipart(msg_chunks, flags=zmq.NOBLOCK)
        except zmq.ZMQError:
            self.exception(".send(): Error")
            return False
        return True

    def _recv(self):
        r"""Receive a message.

        Returns:
            tuple (bool, obj): Success or failure of receive and received
                message.

        """
        if self.socket.closed:
            self.error(".recv(): Socket closed")
            return (False, None)
        try:
            msg_chunks = self.socket.recv_multipart()
        except zmq.ZMQError:
            self.exception(".recv(): Error")
            return (False, None)
        return (True, backwards.unicode2bytes('').join(msg_chunks))


class ZMQInput(ZMQComm):
    r"""Class for handling input via a ZeroMQ socket.

    Args:
        name (str): The environment variable where the socket address is
            stored.
        **kwargs: All additional keywords are passed to ZMQComm.

    """
    def __init__(self, name, **kwargs):
        kwargs['direction'] = 'recv'
        super(ZMQInput, self).__init__(name, **kwargs)
        
        
class ZMQOutput(ZMQComm):
    r"""Class for handling output via a ZeroMQ socket.

    Args:
        name (str): The environment variable where the socket address is
            stored.
        **kwargs: All additional keywords are passed to ZMQComm.

    """
    def __init__(self, name, **kwargs):
        kwargs['direction'] = 'send'
        super(ZMQOutput, self).__init__(name, **kwargs)
