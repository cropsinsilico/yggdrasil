import uuid
import time
import zmq
import threading
import multiprocessing
from cis_interface import backwards
from cis_interface.communication import CommBase
from cis_interface.tools import CisClass


_registered_sockets = dict()
_registered_servers = dict()


_socket_type_pairs = [('PUSH', 'PULL'),
                      ('PUB', 'SUB'),
                      ('REP', 'REQ'),
                      ('ROUTER', 'DEALER'),
                      ('PAIR', 'PAIR')]
_socket_send_types = [t[0] for t in _socket_type_pairs]
_socket_recv_types = [t[1] for t in _socket_type_pairs]
_socket_protocols = ['tcp', 'inproc', 'ipc', 'udp', 'pgm', 'epgm']
_flag_zmq_filter = backwards.unicode2bytes('_ZMQFILTER_')
_default_socket_type = 4
_default_protocol = 'tcp'


def register_socket(socket_type_name, address):
    r"""Register a socket.

    Args:
        socket_type_name (str): Name of the socket type.
        address (str): Socket address.

    """
    global _registered_sockets
    key = '%s_%s' % (socket_type_name, address)
    _registered_sockets[key] = address

    
def unregister_socket(socket_type_name, address):
    r"""Unregister a socket.

    Args:
        socket_type_name (str): Name of the socket type.
        address (str): Socket address.

    """
    global _registered_sockets
    key = '%s_%s' % (socket_type_name, address)
    if key in _registered_sockets:
        del _registered_sockets[key]

        
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


def format_address(protocol, host, port=None):
    r"""Format an address based on its parts.

    Args:
        protocol (str): Communication protocol that should be used.
        host (str): Host that address should point to.
        port (int, optional): Port that address should point to. Defaults to
            None and is not added to the address.

    Returns:
        str: Complete address.

    Raises:
        ValueError: If the protocol is not recognized.

    """
    if host == 'localhost':
        host = '127.0.0.1'
    if protocol in ['inproc', 'ipc']:
        address = "%s://%s" % (protocol, host)
    elif protocol not in _socket_protocols:
        raise ValueError("Unrecognized protocol: %s" % protocol)
    else:
        address = "%s://%s" % (protocol, host)
        if port is not None:
            address += ":%d" % port
    return address

                    
def parse_address(address):
    r"""Split an address into its parts.

    Args:
        address (str): Address to be split.

    Returns:
        dict: Parameters extracted from the address.

    Raises:
        ValueError: If the address dosn't contain '://'.
        ValueError: If the protocol is not supported.

    """
    if '://' not in address:
        raise ValueError("Address must contain '://'")
    protocol, res = address.split('://')
    if protocol not in _socket_protocols:
        raise ValueError("Protocol '%s' not supported." % protocol)
    if protocol in ['inproc', 'ipc']:
        host = res
        port = protocol
    else:
        if ':' in res:
            host, port = res.split(':')
        else:
            host = res
            port = None
    out = dict(protocol=protocol, host=host, port=port)
    return out


def bind_socket(socket, address):
    r"""Bind a socket to an address, getting a random port as necessary.

    Args:
        socket (zmq.Socket): Socket that should be bound.
        address (str): Address that socket should be bound to.

    Returns:
        str: Address that socket was bound to, including random port if one
            was used.

    """
    param = parse_address(address)
    if (param['protocol'] in ['inproc', 'ipc']) or (param['port'] is not None):
        socket.bind(address)
    else:
        port = socket.bind_to_random_port(address)
        address += ":%d" % port
    return address

    
class ZMQProxy(threading.Thread, CisClass):
# class ZMQProxy(multiprocessing.Process):
    r"""Start a proxy in a new thread for a server address. A client-side
    address will be randomly generated.

    Args:
        srv_address (str): Address that should face the server(s).
        context (zmq.Context, optional): ZeroMQ context that should be used.
            Defaults to None and the global context is used.
        protocol (str, optional): Protocol that should be used for the sockets.
            Defaults to None and is set to _default_protocol.
        host (str, optional): Host for socket address. Defaults to 'localhost'.
        **kwargs: Additional keyword arguments are passed to the parent class.

    Attributes:
        srv_address (str): Address that faces the server(s).
        cli_address (str): Address that faces the client(s).
        context (zmq.Context): ZeroMQ context that will be used.
        srv_socket (zmq.Socket): Socket facing client(s).
        cli_socket (zmq.Socket): Socket facing server(s).
        cli_count (int): Number of clients that have connected to this proxy.

    """
    def __init__(self, srv_address, context=None, **kwargs):
        # Get parameters
        srv_param = parse_address(srv_address)
        cli_param = dict()
        for k in ['protocol', 'host', 'port']:
            cli_param[k] = kwargs.pop(k, srv_param[k])
        super(ZMQProxy, self).__init__(**kwargs)
        context = context or zmq.Context.instance()
        # Create new address for the frontend
        if cli_param['protocol'] in ['inproc', 'ipc']:
            cli_param['host'] = str(uuid.uuid4())
        cli_address = format_address(cli_param['protocol'], cli_param['host'])
        frontend = context.socket(zmq.ROUTER)
        self.cli_address = bind_socket(frontend, cli_address)
        self.cli_socket = frontend
        register_socket('ROUTER', self.cli_address)
        # Bind backend
        backend = context.socket(zmq.DEALER)
        self.srv_address = bind_socket(backend, srv_address)
        self.srv_socket = backend
        register_socket('DEALER', self.srv_address)
        # Set up poller
        self.poller = zmq.Poller()
        self.poller.register(frontend, zmq.POLLIN)
        self.cli_count = 0
        self._running = False

    def run(self):
        r"""Run the proxy, handling errors on exit."""
        self._running = True
        self.debug('.run(): Proxy forwarding messages from %s to %s',
                   self.cli_address, self.srv_address)
        try:
            # This version does explicit checking of polls
            while self._running:
                socks = dict(self.poller.poll())
                if socks.get(self.cli_socket) == zmq.POLLIN:
                # out = self.cli_socket.poll(timeout=1, flags=zmq.POLLIN)
                # if out == zmq.POLLIN:
                    message = self.cli_socket.recv_multipart()
                    # print('fowarding', message)
                    self.debug('.run(): forwarding message of size %d from %s',
                               len(message[1]), message[0])
                    # self.srv_socket.send_multipart(message, zmq.NOBLOCK)
                    self.srv_socket.send(message[1], zmq.NOBLOCK)
            # This version does fowarding in a black box
            # zmq.proxy(self.cli_socket, self.srv_socket)
        except zmq.ZMQError:
            self.debug('.run(): Proxy fowarding stopped.')
            pass
        # self.cli_socket.close()
        # self.srv_socket.close()

    def terminate(self):
        r"""Stop the proxy."""
        self._running = False
        if self.cli_socket:
            self.cli_socket.close()
            self.cli_socket = None
        if self.srv_socket:
            self.srv_socket.close()
            self.srv_socket = None
        unregister_socket('ROUTER', self.cli_address)
        unregister_socket('DEALER', self.srv_address)
        if hasattr(super(ZMQProxy, self), 'terminate'):
            super(ZMQProxy, self).terminate()


class ZMQComm(CommBase.CommBase):
    r"""Class for handling I/O using ZeroMQ sockets.

    Args:
        name (str): The environment variable where the socket address is
            stored.
        context (zmq.Context, optional): ZeroMQ context that should be used.
            Defaults to None and the global context is used.
        socket_type (str, optional): The type of socket that should be created.
            Defaults to _default_socket_type. See zmq for all options.
        socket_action (str, optional): The action that the socket should perform.
            Defaults to action based on the direction ('connect' for 'recv',
            'bind' for 'send'.)
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
        socket_action (str, optional): The action that the socket should perform.
        topic_filter (str): Message filter to use when subscribing.
        dealer_identity (str): Identity that should be used to route messages
            to a dealer socket.

    """
    def __init__(self, name, context=None, socket_type=None, socket_action=None,
                 topic_filter='', dealer_identity=None, dont_open=False, **kwargs):
        super(ZMQComm, self).__init__(name, dont_open=True, **kwargs)
        # Client/Server things
        if self.is_client:
            socket_type = 'DEALER'
            socket_action = 'connect'
            self.direction = 'send'
        if self.is_server:
            socket_type = 'DEALER'
            socket_action = 'connect'
            self.direction = 'recv'
        # if self.is_response_client:
        #     socket_action = 'bind'
        # if self.is_response_server:
        #     socket_action = 'connect'
        # Set defaults
        if socket_type is None:
            if self.direction == 'recv':
                socket_type = _socket_recv_types[_default_socket_type]
            elif self.direction == 'send':
                socket_type = _socket_send_types[_default_socket_type]
        if not (self.is_client or self.is_server):
            if socket_type in ['PULL', 'SUB', 'REQ', 'DEALER']:
                self.direction = 'recv'  # connect
            elif socket_type in ['PUSH', 'PUB', 'REP', 'ROUTER']:
                self.direction = 'send'  # bind
        if socket_action is None:
            if self.port in ['inproc', 'ipc']:
                if self.direction == 'recv':
                    socket_action = 'connect'
                elif self.direction == 'send':
                    socket_action = 'bind'
            elif self.port is None:
                socket_action = 'bind'
            else:
                socket_action = 'connect'
        self.context = context or zmq.Context.instance()
        self.socket_type_name = socket_type
        self.socket_type = getattr(zmq, socket_type)
        self.socket_action = socket_action
        self.socket = self.context.socket(self.socket_type)
        self.topic_filter = backwards.unicode2bytes(topic_filter)
        if dealer_identity is None:
            dealer_identity = str(uuid.uuid4())
        self.dealer_identity = backwards.unicode2bytes(dealer_identity)
        self._openned = False
        self._bound = False
        self._recv_identities = set([])
        self._client_proxy = None
        # Reserve/set port by binding
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
    def address_param(self):
        r"""dict: Address parameters."""
        return parse_address(self.address)

    @property
    def protocol(self):
        r"""str: Protocol that socket uses."""
        return self.address_param['protocol']

    @property
    def host(self):
        r"""str: Host that socket is connected to."""
        return self.address_param['host']

    @property
    def port(self):
        r"""str: Port that socket is connected to."""
        return self.address_param['port']

    @classmethod
    def new_comm_kwargs(cls, name, protocol=None, host=None, port=None, **kwargs):
        r"""Initialize communication with new queue.

        Args:
            name (str): Name of new socket.
            protocol (str, optional): The protocol that should be used.
                Defaults to None and is set to _default_protocol. See zmq for
                details.
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
        if protocol is None:
            protocol = _default_protocol
        if host is None:
            if protocol in ['inproc', 'ipc']:
                host = str(uuid.uuid4())
            else:
                host = 'localhost'
        if 'address' not in kwargs:
            kwargs['address'] = format_address(protocol, host, port=port)
        return args, kwargs

    @property
    def opp_address(self):
        r"""str: Address for opposite comm."""
        if self.is_client:
            if self._client_proxy is None:  # pragma: debug
                raise Exception("The client proxy does not yet have an address.")
            return self._client_proxy.srv_address
        else:
            return self.address

    def opp_comm_kwargs(self):
        r"""Get keyword arguments to initialize communication with opposite
        comm object.

        Returns:
            dict: Keyword arguments for opposite comm object.

        """
        kwargs = super(ZMQComm, self).opp_comm_kwargs()
        kwargs['socket_type'] = get_socket_type_mate(self.socket_type_name)
        if self.is_client:
            kwargs['is_server'] = True
        elif self.is_server:
            kwargs['is_client'] = True
        if kwargs['socket_type'] in ['DEALER', 'ROUTER']:
            kwargs['dealer_identity'] = self.dealer_identity
        return kwargs

    def register_socket(self):
        r"""Register a socket."""
        register_socket(self.socket_type_name, self.address)

    def unregister_socket(self):
        r"""Unregister a socket."""
        unregister_socket(self.socket_type_name, self.address)
        
    def bind(self):
        r"""Bind to address, getting random port as necessary."""
        if self.is_open or self._bound:  # pragma: debug
            return
        # Do client things
        if self.is_client and not self._client_proxy:
            self.address = self.get_client_proxy(self.address)
        # Bind to reserve port if that is this sockets action
        if (self.socket_action == 'bind') or (self.port is None):
            self._bound = True
            self.debug('.bind(): Binding %s socket to %s.',
                       self.socket_type_name, self.address)
            try:
                self.address = bind_socket(self.socket, self.address)
            except zmq.ZMQError as e:
                if e.errno == 98:
                    try:
                        self.sleep()
                        self.sleep()
                        self.address = bind_socket(self.socket, self.address)
                    except zmq.ZMQError as e2:
                        if (self.socket_type_name == 'PAIR') and (e2.errno == 98):
                            self.error(("There is already a 'PAIR' socket sending " +
                                        "to %s. Maybe you meant to create a recv " +
                                        "PAIR?") % self.address)
                        raise e2
            # Unbind if action should be connect
            if self.socket_action == 'connect':
                self.unbind()
        else:
            self._bound = False
        if self._bound:
            self.register_socket()

    def get_client_proxy(self, srv_address):
        r"""Create a new client proxy for the specified address."""
        global _registered_servers
        srv_param = parse_address(srv_address)
        if (srv_address not in _registered_servers) or (srv_param['port'] is None):
            proxy = ZMQProxy(srv_address, context=self.context)
            proxy.start()
            _registered_servers[srv_address] = proxy
        _registered_servers[srv_address].cli_count += 1
        self._client_proxy = _registered_servers[srv_address]
        return self._client_proxy.cli_address

    def close_client_proxy(self):
        r"""Sign-off from client proxy, closing the additional sockets if there
        are not more clients."""
        global _registered_servers
        self._client_proxy.cli_count -= 1
        if self._client_proxy.cli_count <= 0:
            self._client_proxy.terminate()
            self._client_proxy.join()
            assert(not self._client_proxy.is_alive())
            if self._client_proxy.srv_address in _registered_servers:
                del _registered_servers[self._client_proxy.srv_address]
        self._client_proxy = None

    def unbind(self):
        r"""Unbind from address."""
        if self._bound:
            self.socket.unbind(self.address)
            self.unregister_socket()
            self._bound = False

    def open(self):
        r"""Open connection by binding/connect to the specified socket."""
        super(ZMQComm, self).open()
        if not self.is_open:
            # Set dealer identity
            if self.socket_type_name == 'DEALER':
                self.socket.setsockopt(zmq.IDENTITY, self.dealer_identity)
            # Bind/connect
            if self.socket_action == 'bind':
                self.bind()
            elif self.socket_action == 'connect':
                # Bind then unbind to get port as necessary
                self.bind()
                self.unbind()
                self.debug('.open(): Connecting %s socket to %s.',
                           self.socket_type_name, self.address)
                self.socket.connect(self.address)
                self.register_socket()
            # Set topic filter
            if self.socket_type_name == 'SUB':
                self.socket.setsockopt(zmq.SUBSCRIBE, self.topic_filter)
            self._openned = True

    def close(self):
        r"""Close connection."""
        if self.is_open or self._bound:
            self.socket.close()
            self._openned = False
            self.unregister_socket()
        if self.is_client and self._client_proxy:
            self.close_client_proxy()
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

    # def _send_multipart(self, msg, **kwargs):
    #     r"""Send a message larger than maxMsgSize in multiple parts.

    #     Args:
    #         msg (str): Message to send.
    #         **kwargs: Additional keyword arguments are passed to _send.

    #     Returns:
    #         bool: Success or failure of sending the message.

    #     """
    #     # flag, _ = self._recv(timeout=self.recv_timeout)
    #     flag, _ = self._recv(timeout=False, flags=0)
    #     if not flag:  # pragma: debug
    #         return flag
    #     flag = self._send(_)
    #     if not flag:
    #         return flag
    #     flag = super(ZMQComm, self)._send_multipart(msg, **kwargs)
    #     return flag

    def _send(self, msg, topic='', identity=None, **kwargs):
        r"""Send a message.

        Args:
            msg (str, bytes): Message to be sent.
            topic (str, optional): Filter that should be sent with the
                message for 'PUB' sockets. Defaults to ''.
            identity (str, optional): Identify of identified worker that
                should be sent for 'ROUTER' sockets. Defaults to
                self.dealer_identity.
            **kwargs: Additional keyword arguments are passed to socket send.

        Returns:
            bool: Success or failure of send.

        """
        if self.is_closed:  # pragma: debug
            self.error(".send(): Socket closed")
            return False
        if identity is None:
            identity = self.dealer_identity
        topic = backwards.unicode2bytes(topic)
        identity = backwards.unicode2bytes(identity)
        if self.socket_type_name == 'PUB':
            total_msg = topic + _flag_zmq_filter + msg
        else:
            total_msg = msg
        # print('(python) sending %d bytes to %s' % (len(total_msg), self.address))
        kwargs.setdefault('flags', zmq.NOBLOCK)
        try:
            if self.socket_type_name == 'ROUTER':
                self.socket.send(identity, zmq.SNDMORE)
            self.socket.send(total_msg, **kwargs)
        except zmq.ZMQError as e:  # pragma: debug
            # if e.errno == 11:
            #     self.debug(".send(): Socket not yet bound on receiving end. " +
            #                "Retrying in %5.2f s." % self.sleeptime)
            #     self.sleep()
            # else:
            self.debug(".send(): Socket could not send. (errno=%d)", e.errno)
            return False
        return True

    # def _recv_multipart(self, *args, **kwargs):
    #     r"""Receive a message sent in multiple parts.

    #     Args:
    #         *args: All arguments are passed to parent _recv_multipart.
    #         **kwargs: All keyword arguments are passed to parent _recv_multipart.

    #     Returns:
    #         tuple (bool, str): The success or failure of receiving a message
    #             and the complete message received.

    #     """
    #     data = backwards.unicode2bytes('CISHANDSHAKE')
    #     nodata = backwards.unicode2bytes('')
    #     flag = self._send(data)
    #     if not flag:  # pragma: debug
    #         return False, nodata
    #     flag, msg = self._recv(timeout=False, flags=0)
    #     if not flag:  # pragma: debug
    #         return False, nodata
    #     if msg != data:
    #         return False, nodata
    #     # kwargs['flags'] = 0
    #     # kwargs['timeout'] = self.timeout
    #     out = super(ZMQComm, self)._recv_multipart(*args, **kwargs)
    #     return out
    
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
        try:
            if self.socket_type_name == 'ROUTER':
                identity = self.socket.recv(flags)
                self._recv_identities.add(identity)
            kwargs.setdefault('flags', flags)
            total_msg = self.socket.recv(**kwargs)
        except zmq.ZMQError:  # pragma: debug
            self.exception(".recv(): Error")
            return (False, None)
        # print('(python) received %d bytes from %s' % (len(total_msg), self.address))
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
