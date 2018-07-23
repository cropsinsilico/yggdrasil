import os
import uuid
import atexit
import threading
import numpy as np
import pandas as pd
from cis_interface import backwards, tools, serialize
from cis_interface.tools import get_CIS_MSG_MAX, CIS_MSG_EOF
from cis_interface.communication import (
    new_comm, get_comm, get_comm_class, determine_suffix)
from cis_interface.schema import register_component


_registered_servers = dict()
_registered_comms = dict()
_server_lock = threading.RLock()
_registry_lock = threading.RLock()


def is_registered(comm_class, key):
    r"""Determine if a comm object has been registered under the specified key.
    
    Args:
        comm_class (str): Comm class to check for the key under.
        key (str): Key that should be checked.

    """
    with _registry_lock:
        global _registered_comms
        if comm_class not in _registered_comms:
            return False
        return (key in _registered_comms[comm_class])


def get_comm_registry(comm_class):
    r"""Get the comm registry for a comm class.

    Args:
        comm_class (str): Comm class to get registry for.

    Returns:
        dict: Dictionary of registered comm objects.

    """
    with _registry_lock:
        if comm_class is None:
            out = {}
        else:
            out = _registered_comms.get(comm_class, {})
    return out


def register_comm(comm_class, key, value):
    r"""Add a comm object to the global registry.

    Args:
        comm_class (str): Comm class to register the object under.
        key (str): Key that should be used to register the object.
        value (obj): Object being registered.

    """
    with _registry_lock:
        global _registered_comms
        if comm_class not in _registered_comms:
            _registered_comms[comm_class] = dict()
        if key not in _registered_comms[comm_class]:
            _registered_comms[comm_class][key] = value


def unregister_comm(comm_class, key, dont_close=False):
    r"""Remove a comm object from the global registry and close it.

    Args:
        comm_class (str): Comm class to check for key under.
        key (str): Key for object that should be removed from the registry.
        dont_close (bool, optional): If True, the comm will be removed from
            the registry, but it won't be closed. Defaults to False.

    Returns:
        bool: True if an object was closed.

    """
    with _registry_lock:
        global _registered_comms
        if comm_class not in _registered_comms:
            return False
        if key not in _registered_comms[comm_class]:
            return False
        value = _registered_comms[comm_class].pop(key)
        if dont_close:
            return False
        out = get_comm_class(comm_class).close_registry_entry(value)
        del value
    return out


def cleanup_comms(comm_class, close_func=None):
    r"""Clean up comms of a certain type.

    Args:
        comm_class (str): Comm class that should be cleaned up.

    Returns:
        int: Number of comms closed.

    """
    count = 0
    if comm_class is None:
        return count
    with _registry_lock:
        global _registered_comms
        if comm_class in _registered_comms:
            keys = [k for k in _registered_comms[comm_class].keys()]
            for k in keys:
                flag = unregister_comm(comm_class, k)
                if flag:  # pragma: debug
                    count += 1
    return count


class CommThreadLoop(tools.CisThreadLoop):
    r"""Thread loop for comms to ensure cleanup.

    Args:
        comm (:class:.CommBase): Comm class that thread is for.
        name (str, optional): Name for the thread. If not provided, one is
            created by combining the comm name and the provided suffix.
        suffix (str, optional): Suffix that should be added to comm name to name
            the thread. Defaults to 'CommThread'.
        **kwargs: Additional keyword arguments are passed to the parent class.

    Attributes:
        comm (:class:.CommBase): Comm class that thread is for.

    """
    def __init__(self, comm, name=None, suffix='CommThread', **kwargs):
        self.comm = comm
        if name is None:
            name = '%s.%s' % (comm.name, suffix)
        # if comm.matlab:
        #     kwargs['daemon'] = True
        super(CommThreadLoop, self).__init__(name=name, **kwargs)

    def on_main_terminated(self):  # pragma: debug
        r"""Actions taken on the backlog thread when the main thread stops."""
        # for i in threading.enumerate():
        #     print(i.name)
        self.debug('is_interface = %s, direction = %s',
                   self.comm.is_interface, self.comm.direction)
        if self.comm.is_interface:
            self.debug('_1st_main_terminated = %s', str(self._1st_main_terminated))
            if self.comm.direction == 'send':
                self._1st_main_terminated = True
                self.comm.send_eof()
                self.comm.close_in_thread(no_wait=True)
                self.debug("Close in thread, closed = %s, nmsg = %d",
                           self.comm.is_closed, self.comm.n_msg)
                return
        super(CommThreadLoop, self).on_main_terminated()


class CommServer(tools.CisThreadLoop):
    r"""Basic server object to keep track of clients.

    Attributes:
        cli_count (int): Number of clients that have connected to this server.

    """
    def __init__(self, srv_address, cli_address=None, **kwargs):
        global _registered_servers
        self.cli_count = 0
        if cli_address is None:
            cli_address = srv_address
        self.srv_address = srv_address
        self.cli_address = cli_address
        super(CommServer, self).__init__('CommServer.%s' % srv_address, **kwargs)
        _registered_servers[self.srv_address] = self

    def add_client(self):
        r"""Increment the client count."""
        global _registered_servers
        _registered_servers[self.srv_address].cli_count += 1
        self.debug("Added client to server: nclients = %d", self.cli_count)

    def remove_client(self):
        r"""Decrement the client count, closing the server if all clients done."""
        global _registered_servers
        self.debug("Removing client from server")
        _registered_servers[self.srv_address].cli_count -= 1
        if _registered_servers[self.srv_address].cli_count <= 0:
            self.debug("Shutting down server")
            self.terminate()
            _registered_servers.pop(self.srv_address)


@register_component
class CommBase(tools.CisClass):
    r"""Class for handling I/O.

    Args:
        name (str): The environment variable where communication address is
            stored.
        address (str, optional): Communication info. Default to None and
            address is taken from the environment variable.
        direction (str, optional): The direction that messages should flow
            through the connection. 'send' if the connection will send
            messages, 'recv' if the connecton will receive messages. Defaults
            to 'send'.
        serializer (:class:.DefaultSerialize, optional): Class with serialize and
            deserialize methods that should be used to process sent and received
            messages. Defaults to None and is constructed using provided
            'serializer_kwargs'.
        serializer_kwargs (dict, optional): Keyword arguments that should be
            passed to :class:.DefaultSerialize to create serializer. Defaults to {}.
        format_str (str, optional): String that should be used to format/parse
            messages. Default to None.
        dont_open (bool, optional): If True, the connection will not be opened.
            Defaults to False.
        is_interface (bool, optional): Set to True if this comm is a Python
            interface binding. Defaults to False.
        recv_timeout (float, optional): Time that should be waited for an
            incoming message before returning None. Defaults to 0 (no wait). A
            value of False indicates that recv should block.
        close_on_eof_recv (bool, optional): If True, the comm will be closed
            when it receives an end-of-file messages. Otherwise, it will remain
            open. Defaults to True.
        close_on_eof_send (bool, optional): If True, the comm will be closed
            after it sends an end-of-file messages. Otherwise, it will remain
            open. Defaults to False.
        single_use (bool, optional): If True, the comm will only be used to
            send/recv a single message. Defaults to False.
        reverse_names (bool, optional): If True, the suffix added to the comm
            with be reversed. Defaults to False.
        no_suffix (bool, optional): If True, no directional suffix will be added
            to the comm name. Defaults to False.
        is_client (bool, optional): If True, the comm is one of many potential
            clients that will be sending messages to one or more servers.
            Defaults to False.
        is_response_client (bool, optional): If True, the comm is a client-side
            response comm. Defaults to False.
        is_server (bool, optional): If True, the commis one of many potential
            servers that will be receiving messages from one or more clients.
            Defaults to False.
        is_response_server (bool, optional): If True, the comm is a server-side
            response comm. Defaults to False.
        recv_converter (func, optional): Converter that should be used on
            received objects. Defaults to None.
        send_converter (func, optional): Converter that should be used on
            sent objects. Defaults to None.
        comm (str, optional): The comm that should be created. This only serves
            as a check that the correct class is being created. Defaults to None.
        matlab (bool, optional): True if the comm will be accessed by Matlab
            code. Defaults to False.
        **kwargs: Additional keywords arguments are passed to parent class.

    Attributes:
        name (str): The environment variable where communication address is
            stored.
        address (str): Communication info.
        direction (str): The direction that messages should flow through the
            connection.
        serializer (:class:.DefaultSerialize): Object that will be used to
            serialize/deserialize messages to/from python objects.
        is_interface (bool): True if this comm is a Python interface binding.
        recv_timeout (float): Time that should be waited for an incoming
            message before returning None.
        close_on_eof_recv (bool): If True, the comm will be closed when it
            receives an end-of-file messages. Otherwise, it will remain open.
        close_on_eof_send (bool): If True, the comm will be closed after it
            sends an end-of-file messages. Otherwise, it will remain open.
        single_use (bool): If True, the comm will only be used to send/recv a
            single message.
        is_client (bool): If True, the comm is one of many potential clients
            that will be sending messages to one or more servers.
        is_response_client (bool): If True, the comm is a client-side response
            comm.
        is_server (bool): If True, the comm is one of many potential servers
            that will be receiving messages from one or more clients.
        is_response_server (bool): If True, the comm is a server-side response
            comm.
        is_file (bool): True if the comm accesses a file.
        recv_converter (func): Converter that should be used on received objects.
        send_converter (func): Converter that should be used on sent objects.
        matlab (bool): True if the comm will be accessed by Matlab code.

    Raises:
        RuntimeError: If the comm class is not installed.
        RuntimeError: If there is not an environment variable with the specified
            name.
        ValueError: If directions is not 'send' or 'recv'.

    """

    _commtype = 'default'
    _schema_type = 'comm'
    _schema = {'name': {'type': 'string', 'required': True},
               'dtype': {'type': 'string', 'required': False},  # TODO: add values
               'units': {'type': 'string', 'required': False},  # TODO: add values
               'format_str': {'type': 'string', 'required': False},
               'as_array': {'type': 'boolean', 'required': False},
               'field_names': {'type': 'list', 'required': False,
                               'schema': {'type': 'string'}},
               'field_units': {'type': 'list', 'required': False,
                               'schema': {'type': 'string'}},  # TODO: coerce units
               'stype': {'type': 'integer', 'required': False}}

    def __init__(self, name, address=None, direction='send',
                 dont_open=False, is_interface=False, recv_timeout=0.0,
                 close_on_eof_recv=True, close_on_eof_send=False,
                 single_use=False, reverse_names=False, no_suffix=False,
                 is_client=False, is_response_client=False,
                 is_server=False, is_response_server=False,
                 recv_converter=None, send_converter=None,
                 comm=None, matlab=False, **kwargs):
        self._comm_class = None
        if comm is not None:
            assert(comm == self.comm_class)
        super(CommBase, self).__init__(name, **kwargs)
        if not self.__class__.is_installed():
            raise RuntimeError("Comm class %s not installed" % self.__class__)
        suffix = determine_suffix(no_suffix=no_suffix,
                                  reverse_names=reverse_names,
                                  direction=direction)
        self.name_base = name
        self.suffix = suffix
        self._name = name + suffix
        if address is None:
            if self.name not in os.environ:
                raise RuntimeError('Cannot see %s in env.' % self.name)
            self.address = os.environ[self.name]
        else:
            self.address = address
        self.direction = direction
        self.is_client = is_client
        self.is_server = is_server
        self.is_response_client = is_response_client
        self.is_response_server = is_response_server
        self.is_file = False
        self.matlab = matlab
        self.recv_converter = recv_converter
        self.send_converter = send_converter
        self._server = None
        self.is_interface = is_interface
        self.recv_timeout = recv_timeout
        self.close_on_eof_recv = close_on_eof_recv
        self.close_on_eof_send = close_on_eof_send
        self._last_header = None
        self._work_comms = {}
        self.single_use = single_use
        self._used = False
        self._multiple_first_send = True
        self._n_sent = 0
        self._n_recv = 0
        self._bound = False
        self._last_send = None
        self._last_recv = None
        self._timeout_drain = False
        self._server_class = CommServer
        self._server_kwargs = {}
        self._send_serializer = True
        if self.single_use and (not self.is_response_server):
            self._send_serializer = False
        # Add interface tag
        if self.is_interface:
            self._name += '_I'
        # if self.is_interface:
        #     self._timeout_drain = False
        # else:
        #     self._timeout_drain = self.timeout
        self._closing_event = threading.Event()
        self._closing_thread = tools.CisThread(target=self.linger_close,
                                               # daemon=self.matlab,
                                               name=self.name + '.ClosingThread')
        self._eof_recv = threading.Event()
        self._eof_sent = threading.Event()
        self._field_backlog = dict()
        if self.single_use:
            self._eof_recv.set()
            self._eof_sent.set()
        if self.is_response_client or self.is_response_server:
            self._eof_sent.set()  # Don't send EOF, these are single use
        if self.is_interface:
            atexit.register(self.atexit)
        self._init_before_open(**kwargs)
        if dont_open:
            self.bind()
        else:
            self.open()

    def _init_before_open(self, serializer=None, serializer_kwargs=None,
                          serializer_type=None, **kwargs):
        r"""Initialization steps that should be performed after base class, but
        before the comm is opened."""
        seri_kws = ['format_str', 'as_array', 'field_names', 'field_units',
                    'stype']
        if serializer is not None:
            self.serializer = serializer
        else:
            if serializer_kwargs is None:
                serializer_kwargs = {}
            serializer_kwargs.setdefault('stype', serializer_type)
            for k in seri_kws:
                if serializer_kwargs.get(k, None) is None:
                    serializer_kwargs[k] = kwargs.pop(k, None)
            self.serializer = serialize.get_serializer(**serializer_kwargs)

    def printStatus(self, nindent=0):
        r"""Print status of the communicator."""
        prefix = nindent * '\t'
        print('%s%s:' % (prefix, self.name))
        prefix += '\t'
        print('%s%-15s: %s' % (prefix, 'address', self.address))
        print('%s%-15s: %s' % (prefix, 'direction', self.direction))
        print('%s%-15s: %s' % (prefix, 'open', self.is_open))
        print('%s%-15s: %s' % (prefix, 'nsent', self._n_sent))
        print('%s%-15s: %s' % (prefix, 'nrecv', self._n_recv))

    @classmethod
    def is_installed(cls):
        r"""bool: Is the comm installed."""
        return True

    @property
    def maxMsgSize(self):
        r"""int: Maximum size of a single message that should be sent."""
        return get_CIS_MSG_MAX()

    @property
    def empty_msg(self):
        r"""str: Empty message."""
        return backwards.unicode2bytes('')

    @property
    def comm_class(self):
        r"""str: Name of communication class."""
        if self._comm_class is None:
            self._comm_class = str(self.__class__).split("'")[1].split(".")[-1]
        return self._comm_class

    @classmethod
    def underlying_comm_class(self):
        r"""str: Name of underlying communication class."""
        return None

    @classmethod
    def close_registry_entry(cls, value):
        r"""Close a registry entry."""
        return False

    @classmethod
    def cleanup_comms(cls):
        r"""Cleanup registered comms of this class."""
        return cleanup_comms(cls.underlying_comm_class())

    @classmethod
    def comm_registry(cls):
        r"""dict: Registry of comms of this class."""
        return get_comm_registry(cls.underlying_comm_class())

    def register_comm(self, key, value):
        r"""Register a comm."""
        self.debug("Registering comm: %s", key)
        register_comm(self.comm_class, key, value)

    def unregister_comm(self, key, dont_close=False):
        r"""Unregister a comm."""
        unregister_comm(self.comm_class, key, dont_close=dont_close)

    @classmethod
    def comm_count(cls):
        r"""int: Number of communication connections."""
        out = len(cls.comm_registry())
        if out > 0:
            print(cls, cls.comm_registry())
        return out

    @classmethod
    def new_comm_kwargs(cls, *args, **kwargs):
        r"""Get keyword arguments for new comm."""
        kwargs.setdefault('address', 'address')
        return args, kwargs

    @classmethod
    def new_comm(cls, name, *args, **kwargs):
        r"""Initialize communication with new queue."""
        env = kwargs.get('env', {})
        if name in env:
            kwargs.setdefault('address', env[name])
        elif name in os.environ:
            kwargs.setdefault('address', os.environ[name])
        new_comm_class = kwargs.pop('new_comm_class', None)
        args, kwargs = cls.new_comm_kwargs(name, *args, **kwargs)
        if new_comm_class is not None:
            new_cls = get_comm_class(new_comm_class)
            return new_cls(*args, **kwargs)
        return cls(*args, **kwargs)

    @property
    def opp_address(self):
        r"""str: Address for opposite comm."""
        return self.address

    @property
    def opp_comms(self):
        r"""dict: Name/address pairs for opposite comms."""
        return {self.name: self.opp_address}

    def opp_comm_kwargs(self):
        r"""Get keyword arguments to initialize communication with opposite
        comm object.

        Returns:
            dict: Keyword arguments for opposite comm object.

        """
        kwargs = {'comm': self.comm_class}
        kwargs['address'] = self.opp_address
        kwargs['serializer'] = self.serializer
        if self.direction == 'send':
            kwargs['direction'] = 'recv'
        else:
            kwargs['direction'] = 'send'
        return kwargs

    def bind(self):
        r"""Bind in place of open."""
        if self.is_client:
            self.signon_to_server()

    def open(self):
        r"""Open the connection."""
        self.bind()

    def _close(self, *args, **kwargs):
        r"""Close the connection."""
        pass

    def close(self, skip_base=False, linger=False):
        r"""Close the connection.

        Args:
            skip_base (bool, optional): If True, don't drain messages or remove
                work comms.
            linger (bool, optional): If True, drain messages before closing the
                comm. Defaults to False.

        """
        if (not skip_base):
            self.debug('')
            if linger and self.is_open:
                self.linger()
            else:
                self._closing_thread.set_terminated_flag()
                linger = False
        if skip_base:
            self._close(linger=linger)
            return
        # Close with lock
        with self._closing_thread.lock:
            self._close(linger=linger)
            if not skip_base:
                self._n_sent = 0
                self._n_recv = 0
                if self.is_client:
                    self.debug("Signing off from server")
                    self.signoff_from_server()
                if len(self._work_comms) > 0:
                    self.debug("Cleaning up %d work comms", len(self._work_comms))
                    keys = [k for k in self._work_comms.keys()]
                    for c in keys:
                        self.remove_work_comm(c, linger=linger)
                    self.debug("Finished cleaning up work comms")
        self.debug("done")

    def close_in_thread(self, no_wait=False, timeout=None):
        r"""In a new thread, close the comm when it is empty.

        Args:
            no_wait (bool, optional): If True, don't wait for closing thread
                to stop.
            timeout (float, optional): Time that should be waited for the comm
                to close. Defaults to None and is set to self.timeout. If False,
                this will block until the comm is closed.

        """
        if self.matlab:  # pragma: matlab
            self.linger_close()
            self._closing_thread.set_terminated_flag()
        self.debug("current_thread = %s", threading.current_thread().name)
        try:
            self._closing_thread.start()
            _started_thread = True
        except RuntimeError:  # pragma: debug
            _started_thread = False
        if self._closing_thread.was_started and (not no_wait):  # pragma: debug
            self._closing_thread.wait(key=str(uuid.uuid4()), timeout=timeout)
            if _started_thread and not self._closing_thread.was_terminated:
                self.debug("Closing thread took too long")
                self.close()

    def linger_close(self):
        r"""Wait for messages to drain, then close."""
        self.close(linger=True)

    def linger(self):
        r"""Wait for messages to drain."""
        self.debug('')
        if self.direction == 'recv':
            self.wait_for_confirm(timeout=self._timeout_drain)
        else:
            self.drain_messages(variable='n_msg_send')
            self.wait_for_confirm(timeout=self._timeout_drain)
        self.debug("Finished")

    def matlab_atexit(self):  # pragma: matlab
        r"""Close operations including draining receive."""
        if self.direction == 'recv':
            while self.recv(timeout=0)[0]:
                self.sleep()
        else:
            self.send_eof()
        self.linger_close()

    def atexit(self):  # pragma: debug
        r"""Close operations."""
        self.debug('atexit begins')
        self.close()
        self.debug('atexit finished: closed=%s, n_msg=%d, close_alive=%s',
                   self.is_closed, self.n_msg,
                   self._closing_thread.is_alive())

    @property
    def is_open(self):
        r"""bool: True if the connection is open."""
        return False

    @property
    def is_closed(self):
        r"""bool: True if the connection is closed."""
        return (not self.is_open)

    @property
    def is_confirmed_send(self):
        r"""bool: True if all sent messages have been confirmed."""
        return True

    @property
    def is_confirmed_recv(self):
        r"""bool: True if all received messages have been confirmed."""
        return True

    @property
    def is_confirmed(self):
        r"""bool: True if all messages have been confirmed."""
        if self.direction == 'recv':
            return self.is_confirmed_recv
        else:
            return self.is_confirmed_send

    def wait_for_confirm(self, timeout=None, direction=None,
                         active_confirm=False, noblock=False):
        r"""Sleep until all messages are confirmed."""
        self.debug('')
        if direction is None:
            direction = self.direction
        T = self.start_timeout(t=timeout, key_suffix='.wait_for_confirm')
        flag = False
        while (not T.is_out) and (not getattr(self, 'is_confirmed_%s' % direction)):
            if active_confirm:
                flag = self.confirm(direction=direction, noblock=noblock)
                if flag:
                    break
            self.sleep()
        self.stop_timeout(key_suffix='.wait_for_confirm')
        if not flag:
            flag = getattr(self, 'is_confirmed_%s' % direction)
        self.debug('Done confirming')
        return flag

    def confirm(self, direction=None, noblock=False):
        r"""Confirm message."""
        if direction is None:
            direction = self.direction
        if direction == 'send':
            out = self.confirm_send(noblock=noblock)
        else:
            out = self.confirm_recv(noblock=noblock)
        return out

    def confirm_send(self, noblock=False):
        r"""Confirm that sent message was received."""
        return noblock

    def confirm_recv(self, noblock=False):
        r"""Confirm that message was received."""
        return noblock

    @property
    def n_msg(self):
        r"""int: The number of messages in the connection."""
        if self.direction == 'recv':
            return self.n_msg_recv
        else:
            return self.n_msg_send

    @property
    def n_msg_recv(self):
        r"""int: The number of incoming messages in the connection."""
        return 0

    @property
    def n_msg_send(self):
        r"""int: The number of outgoing messages in the connection."""
        return 0

    @property
    def n_msg_recv_drain(self):
        r"""int: The number of incoming messages in the connection to drain."""
        return self.n_msg_recv

    @property
    def n_msg_send_drain(self):
        r"""int: The number of outgoing messages in the connection to drain."""
        return self.n_msg_send

    @property
    def eof_msg(self):
        r"""str: Message indicating EOF."""
        return backwards.unicode2bytes(CIS_MSG_EOF)

    def is_eof(self, msg):
        r"""Determine if a message is an EOF.

        Args:
            msg (obj): Message object to be tested.

        Returns:
            bool: True if the message indicates an EOF, False otherwise.

        """
        out = (isinstance(msg, backwards.bytes_type) and (msg == self.eof_msg))
        return out
    
    @property
    def empty_obj_recv(self):
        r"""obj: Empty message object."""
        emsg, _ = self.serializer.deserialize(self.empty_msg)
        if (self.recv_converter is not None):
            emsg = self.recv_converter(emsg)
        return emsg

    def is_empty_recv(self, msg):
        r"""Check if a received message object is empty.

        Args:
            msg (obj): Message object.

        Returns:
            bool: True if the object is empty, False otherwise.

        """
        if self.is_eof(msg):
            return False
        return (msg == self.empty_obj_recv)
    
    def chunk_message(self, msg):
        r"""Yield chunks of message of size maxMsgSize

        Args:
            msg (str, bytes): Raw message bytes to be chunked.

        Returns:
            str: Chunks of message.

        """
        prev = 0
        while prev < len(msg):
            next = min(prev + self.maxMsgSize, len(msg))
            yield msg[prev:next]
            prev = next

    # CLIENT/SERVER METHODS
    def server_exists(self, srv_address):
        r"""Determine if a server exists.

        Args:
            srv_address (str): Address of server comm.

        Returns:
            bool: True if a server with the provided address exists, False
                otherwise.

        """
        global _registered_servers
        return (srv_address in _registered_servers)

    def new_server(self, srv_address):
        r"""Create a new server.

        Args:
            srv_address (str): Address of server comm.

        """
        return self._server_class(srv_address, **self._server_kwargs)

    def signon_to_server(self):
        r"""Add a client to an existing server or create one."""
        with _server_lock:
            global _registered_servers
            if self._server is None:
                if not self.server_exists(self.address):
                    self.debug("Creating new server")
                    self._server = self.new_server(self.address)
                    self._server.start()
                else:
                    self._server = _registered_servers[self.address]
                self._server.add_client()
                self.address = self._server.cli_address

    def signoff_from_server(self):
        r"""Remove a client from the server."""
        with _server_lock:
            if self._server is not None:
                self.debug("Signing off")
                self._server.remove_client()
                self._server = None

    # TEMP COMMS
    @property
    def get_work_comm_kwargs(self):
        r"""dict: Keyword arguments for an existing work comm."""
        return dict(comm=self.comm_class, direction='recv',
                    recv_timeout=self.recv_timeout,
                    is_interface=self.is_interface,
                    single_use=True)

    @property
    def create_work_comm_kwargs(self):
        r"""dict: Keyword arguments for a new work comm."""
        return dict(comm=self.comm_class, direction='send',
                    recv_timeout=self.recv_timeout,
                    is_interface=self.is_interface,
                    uuid=str(uuid.uuid4()), single_use=True)

    def get_work_comm(self, header, **kwargs):
        r"""Get temporary work comm, creating as necessary.

        Args:
            header (dict): Information that will be sent in the message header
                to the work comm.
            **kwargs: Additional keyword arguments are passed to header2workcomm.

        Returns:
            :class:.CommBase: Work comm.

        """
        c = self._work_comms.get(header['id'], None)
        if c is not None:
            return c
        c = self.header2workcomm(header, **kwargs)
        self.add_work_comm(c)
        return c

    def create_work_comm(self, work_comm_name=None, **kwargs):
        r"""Create a temporary work comm.

        Args:
            work_comm_name (str, optional): Name that should be used for the
                work comm. If not provided, one is created from the header id
                and the comm class.
            **kwargs: Keyword arguments for new_comm that should override
                work_comm_kwargs.

        Returns:
            :class:.CommBase: Work comm.

        """
        kws = self.create_work_comm_kwargs
        kws.update(**kwargs)
        if work_comm_name is None:
            cls = kws.get("comm", tools.get_default_comm())
            work_comm_name = 'temp_%s_%s.%s' % (cls, kws['direction'], kws['uuid'])
        c = new_comm(work_comm_name, **kws)
        self.add_work_comm(c)
        return c

    def add_work_comm(self, comm):
        r"""Add work comm to dict.

        Args:
            comm (:class:.CommBase): Comm that should be added.

        Raises:
            KeyError: If there is already a comm associated with the key.

        """
        key = comm.uuid
        if key in self._work_comms:
            raise KeyError("Comm already registered with key %s." % key)
        self._work_comms[key] = comm

    def remove_work_comm(self, key, in_thread=False, linger=False):
        r"""Close and remove a work comm.

        Args:
            key (str): Key of comm that should be removed.
            in_thread (bool, optional): If True, close the work comm in a thread.
                Defaults to False.
            linger (bool, optional): If True, drain messages before closing the
                comm. Defaults to False.

        """
        if key not in self._work_comms:
            return
        if not in_thread:
            c = self._work_comms.pop(key)
            c.close(linger=linger)
        else:  # pragma: debug
            # c = self._work_comms[key]
            # c.close_in_thread(no_wait=True)
            raise Exception("Closing in thread not recommended")

    def workcomm2header(self, work_comm, **kwargs):
        r"""Get header information from a comm.

        Args:
            work_comm (:class:.CommBase): Work comm that header describes.
            **kwargs: Additional keyword arguments are added to the header.

        Returns:
            dict: Header information that will be sent with a message.

        """
        header_kwargs = kwargs
        header_kwargs['address'] = work_comm.address
        header_kwargs['id'] = work_comm.uuid
        return header_kwargs

    def header2workcomm(self, header, work_comm_name=None, **kwargs):
        r"""Get a work comm based on header info.

        Args:
            header (dict): Information that will be sent in the message header
                to the work comm.
            work_comm_name (str, optional): Name that should be used for the
                work comm. If not provided, one is created from the header id
                and the comm class.
            **kwargs: Additional keyword arguments are added to the returned
                dictionary.

        Returns:
            :class:.CommBase: Work comm.

        """
        kws = self.get_work_comm_kwargs
        kws.update(**kwargs)
        kws['uuid'] = header['id']
        kws['address'] = header['address']
        if work_comm_name is None:
            cls = kws.get("comm", tools.get_default_comm())
            work_comm_name = 'temp_%s_%s.%s' % (
                cls, kws['direction'], header['id'])
        c = get_comm(work_comm_name, **kws)
        return c

    # SEND METHODS
    def _safe_send(self, *args, **kwargs):
        r"""Send message checking if is 1st message and then waiting."""
        if (not self._used) and self._multiple_first_send:
            out = self._send_1st(*args, **kwargs)
        else:
            with self._closing_thread.lock:
                if self.is_closed:  # pragma: debug
                    return False
                out = self._send(*args, **kwargs)
        if out:
            self._n_sent += 1
            self._last_send = backwards.clock_time()
        return out
    
    def _send_1st(self, *args, **kwargs):
        r"""Send first message until it succeeds."""
        with self._closing_thread.lock:
            if self.is_closed:  # pragma: debug
                return False
            flag = self._send(*args, **kwargs)
        T = self.start_timeout(key_suffix='._send_1st')
        self.suppress_special_debug = True
        while (not T.is_out) and (self.is_open) and (not flag):  # pragma: debug
            with self._closing_thread.lock:
                if not self.is_open:
                    break
                flag = self._send(*args, **kwargs)
            if flag or (self.is_closed):
                break
            self.sleep()
        self.stop_timeout(key_suffix='._send_1st')
        self.suppress_special_debug = False
        return flag
        
    def _send(self, msg, *args, **kwargs):
        r"""Raw send. Should be overridden by inheriting class."""
        raise NotImplementedError("_send method needs implemented.")

    def _send_multipart(self, msg, **kwargs):
        r"""Send a message larger than maxMsgSize in multiple parts.

        Args:
            msg (str): Message to send.
            **kwargs: Additional keyword arguments are apssed to _send.

        Returns:
            bool: Success or failure of sending the message.

        """
        nsent = 0
        ret = True
        for imsg in self.chunk_message(msg):
            if self.is_closed:  # pragma: debug
                self.error("._send_multipart(): Connection closed.")
                return False
            ret = self._safe_send(imsg, **kwargs)
            if not ret:  # pragma: debug
                self.debug("Send interupted at %d of %d bytes.",
                           nsent, len(msg))
                break
            nsent += len(imsg)
            self.debug("%d of %d bytes sent", nsent, len(msg))
        if ret and len(msg) > 0:
            self.debug("%d bytes completed", len(msg))
        return ret

    def _send_multipart_worker(self, msg, info, **kwargs):
        r"""Send multipart message to the worker comm identified.

        Args:
            msg (str): Message to be sent.
            info (dict): Information about the outgoing message.
            **kwargs: Additional keyword arguments are passed to the
                workcomm _send_multipart method.

        Returns:
            bool: Success or failure of sending the message.

        """
        workcomm = self.get_work_comm(info)
        ret = workcomm._send_multipart(msg, **kwargs)
        # self.remove_work_comm(workcomm.uuid, in_thread=True)
        return ret
            
    def on_send_eof(self):
        r"""Actions to perform when EOF being sent.

        Returns:
            bool: True if EOF message should be sent, False otherwise.

        """
        msg_s = backwards.unicode2bytes(self.eof_msg)
        with self._closing_thread.lock:
            if not self._eof_sent.is_set():
                self._eof_sent.set()
            else:  # pragma: debug
                return False, msg_s
        return True, msg_s

    def on_send(self, msg, header_kwargs=None):
        r"""Process message to be sent including handling serializing
        message and handling EOF.

        Args:
            msg (obj): Message to be sent
            header_kwargs (dict, optional): Keyword arguments that should be
                added to the header.

        Returns:
            tuple (bool, str, dict): Truth of if message should be sent, raw
                bytes message to send, and header info contained in the message.

        """
        work_comm = None
        if self.is_closed:
            self.debug('Comm closed')
            return False, self.empty_msg, work_comm
        if len(msg) == 1:
            msg = msg[0]
        if isinstance(msg, backwards.bytes_type) and (msg == self.eof_msg):
            flag, msg_s = self.on_send_eof()
        else:
            flag = True
            add_sinfo = (self._send_serializer and (not self.is_file))
            # Covert object
            if self.send_converter is not None:
                msg_ = self.send_converter(msg)
            else:
                msg_ = msg
            # Guess at serializer if not yet set
            if add_sinfo:
                self.serializer.update_from_message(msg_)
                self.debug('Sending sinfo: %s', self.serializer.serializer_info)
            # Serialize
            msg_s = self.serializer.serialize(msg_, header_kwargs=header_kwargs,
                                              add_serializer_info=add_sinfo)
            # Create work comm if message too large to be sent all at once
            if (len(msg_s) > self.maxMsgSize) and (self.maxMsgSize != 0):
                if header_kwargs is None:
                    header_kwargs = dict()
                work_comm = self.create_work_comm()
                # if 'address' not in header_kwargs:
                #     work_comm = self.create_work_comm()
                # else:
                #     work_comm = self.get_work_comm(header_kwargs)
                header_kwargs = self.workcomm2header(work_comm, **header_kwargs)
                msg_s = self.serializer.serialize(
                    msg_, header_kwargs=header_kwargs,
                    add_serializer_info=add_sinfo)
        return flag, msg_s, header_kwargs

    def send(self, *args, **kwargs):
        r"""Send a message.

        Args:
            *args: All arguments are assumed to be part of the message.
            **kwargs: All keywords arguments are passed to comm _send method.

        Returns:
            bool: Success or failure of send.

        """
        if self.single_use and self._used:  # pragma: debug
            raise RuntimeError("This comm is single use and it was already used.")
        try:
            ret = self.send_multipart(args, **kwargs)
            if ret:
                self._used = True
                self._send_serializer = False
        except BaseException:
            self.exception('Failed to send.')
            return False
        if self.single_use and self._used:
            self.debug('Closing single use send comm [DISABLED]')
            # self.linger_close()
            # self.close_in_thread(no_wait=True)
        elif ret and self._eof_sent.is_set() and self.close_on_eof_send:
            self.debug('Close on send EOF')
            self.linger_close()
            # self.close_in_thread(no_wait=True, timeout=False)
        return ret

    def send_multipart(self, msg, header_kwargs=None, **kwargs):
        r"""Send a multipart message. If the message is smaller than maxMsgSize,
        it is sent using _send, otherwise it is sent to a worker comm using
        _send_multipart_worker.

        Args:
            msg (obj): Message to be sent.
            header_kwargs (dict, optional): Keyword arguments that should be
                added to the header.
            **kwargs: Additional keyword arguments are passed to _send or
                _send_multipart_worker.

        Returns:
            bool: Success or failure of send.
        
        """
        # Create serialized message that should be sent
        flag, msg_s, header = self.on_send(msg, header_kwargs=header_kwargs)
        if not flag:
            return flag
        msg_len = len(msg_s)
        # Sent first part of message
        self.special_debug('Sending %d bytes', msg_len)
        if (msg_len < self.maxMsgSize) or (self.maxMsgSize == 0):
            flag = self._safe_send(msg_s, **kwargs)
        else:
            flag = self._safe_send(msg_s[:self.maxMsgSize])
            if flag:
                # Send remainder of message using work comm
                flag = self._send_multipart_worker(msg_s[self.maxMsgSize:],
                                                   header, **kwargs)
            else:  # pragma: debug
                self.special_debug("Sending message header failed.")
        if flag:
            self.debug('Sent %d bytes', msg_len)
        else:
            self.special_debug('Failed to send %d bytes', msg_len)
        return flag

    def send_nolimit(self, *args, **kwargs):
        r"""Alias for send."""
        return self.send(*args, **kwargs)

    def send_eof(self, *args, **kwargs):
        r"""Send the EOF message as a short message.
        
        Args:
            *args: All arguments are passed to comm send.
            **kwargs: All keywords arguments are passed to comm send.

        Returns:
            bool: Success or failure of send.

        """
        return self.send(self.eof_msg, *args, **kwargs)
        # with self._closing_thread.lock:
        #     if not self._eof_sent.is_set():
        #         self._eof_sent.set()
        #         return self.send(self.eof_msg, *args, **kwargs)
        # return False
        
    def send_nolimit_eof(self, *args, **kwargs):
        r"""Alias for send_eof."""
        return self.send_eof(*args, **kwargs)

    # RECV METHODS
    def _safe_recv(self, *args, **kwargs):
        r"""Safe receive that does things for all comm classes."""
        with self._closing_thread.lock:
            if self.is_closed:
                return (False, self.empty_msg)
            out = self._recv(*args, **kwargs)
        if out[0] and out[1]:
            self._n_recv += 1
            self._last_recv = backwards.clock_time()
        return out

    def _recv(self, *args, **kwargs):
        r"""Raw recv. Should be overridden by inheriting class."""
        raise NotImplementedError("_recv method needs implemented.")

    def _recv_multipart(self, data, leng_exp, **kwargs):
        r"""Receive a message larger than CIS_MSG_MAX that is sent in multiple
        parts.

        Args:
            data (str): Initial data received.
            leng_exp (int): Size of message expected.
            **kwargs: All keyword arguments are passed to _recv.

        Returns:
            tuple (bool, str): The success or failure of receiving a message
                and the complete message received.

        """
        ret = True
        while len(data) < leng_exp:
            payload = self._safe_recv(**kwargs)
            if not payload[0]:  # pragma: debug
                self.debug("Read interupted at %d of %d bytes.",
                           len(data), leng_exp)
                ret = False
                break
            data = data + payload[1]
            # if len(payload[1]) == 0:
            #     self.sleep()
        payload = (ret, data)
        self.debug("Read %d bytes", len(data))
        return payload

    def _recv_multipart_worker(self, info, **kwargs):
        r"""Receive a message in multiple parts from a worker comm.

        Args:
            info (dict): Information about the incoming message.
            **kwargs: Additional keyword arguments are passed to the
                workcomm _recv_multipart method.

        Returns:
            tuple (bool, str): The success or failure of receiving a message
                and the complete message received.

        """
        workcomm = self.get_work_comm(info)
        out = workcomm._recv_multipart(info['body'], info['size'], **kwargs)
        # self.remove_work_comm(info['id'], linger=True)
        return out
        
    def on_recv_eof(self):
        r"""Actions to perform when EOF received.

        Returns:
            bool: Flag that should be returned for EOF.

        """
        self.debug("Received EOF")
        self._eof_recv.set()
        if self.close_on_eof_recv:
            self.debug("Lingering close on EOF Received")
            self.linger_close()
            return False
        else:
            return True

    def on_recv(self, s_msg, second_pass=False):
        r"""Process raw received message including handling deserializing
        message and handling EOF.

        Args:
            s_msg (bytes, str): Raw bytes message.
            second_pass (bool, optional): If True, this is the second pass for
                a message and _last_header will not be set. Defaults to False.

        Returns:
            tuple (bool, str, dict): Success or failure, processed message, and
                header information.

        """
        flag = True
        msg_, header = self.serializer.deserialize(s_msg)
        if self.is_eof(msg_):
            flag = self.on_recv_eof()
            msg = msg_
        elif ((self.recv_converter is not None) and
              (not header.get('incomplete', False))):
            self.debug("Converting message")
            msg = self.recv_converter(msg_)
        else:
            msg = msg_
        if second_pass:
            header = self._last_header
            header['incomplete'] = False
        else:
            self._last_header = header
        if not header.get('incomplete', False):
            # if not self._used:
            #     self.serializer = serialize.get_serializer(**header)
            #     msg, _ = self.serializer.deserialize(s_msg)
            self._used = True
        return flag, msg, header

    def recv(self, *args, **kwargs):
        r"""Receive a message.

        Args:
            *args: All arguments are passed to comm _recv method.
            **kwargs: All keywords arguments are passed to comm _recv method.

        Returns:
            tuple (bool, obj): Success or failure of receive and received
                message.

        """
        if self.single_use and self._used:
            raise RuntimeError("This comm is single use and it was already used.")
        if self.is_closed:
            self.debug('Comm closed')
            return (False, None)
        try:
            flag, msg = self.recv_multipart(*args, **kwargs)
        except BaseException:
            self.exception('Failed to recv.')
            return (False, None)
        if self.single_use and self._used:
            self.linger_close()
        return (flag, msg)

    def recv_multipart(self, *args, **kwargs):
        r"""Receive a multipart message. If a message is received without a
        header, it assumed to be complete. Otherwise, the message is received
        in parts from a worker comm initialized by the sender.

        Args:
            *args: All arguments are passed to comm _recv method.
            **kwargs: All keywords arguments are passed to comm _recv method.

        Returns:
            tuple (bool, str): Success or failure of receive and received
                message.

        """
        # Receive first part of message
        flag, s_msg = self._safe_recv(*args, **kwargs)
        if not flag:
            return flag, s_msg
        # Parse message
        flag, msg, header = self.on_recv(s_msg)
        if not flag:
            if not header.get('eof', False):  # pragma: debug
                self.debug("Failed to receive message header.")
            return flag, msg
        # Receive remainder of message that was not received
        if header.get('incomplete', False):
            header['body'] = msg
            flag, s_msg = self._recv_multipart_worker(header, **kwargs)
            if not flag:  # pragma: debug
                return flag, s_msg
            # Parse complete message
            flag, msg, header2 = self.on_recv(s_msg, second_pass=True)
        if flag and len(s_msg) > 0:
            self.debug('%d bytes received', len(s_msg))
        return flag, msg
        
    def recv_nolimit(self, *args, **kwargs):
        r"""Alias for recv."""
        return self.recv(*args, **kwargs)

    def drain_messages(self, direction=None, timeout=None, variable=None):
        r"""Sleep while waiting for messages to be drained."""
        self.debug('')
        if direction is None:
            direction = self.direction
        if variable is None:
            variable = 'n_msg_%s_drain' % direction
        if timeout is None:
            timeout = self._timeout_drain
        if not hasattr(self, variable):
            raise ValueError("No attribute named '%s'" % variable)
        Tout = self.start_timeout(timeout, key_suffix='.drain_messages')
        while (not Tout.is_out) and self.is_open:
            n_msg = getattr(self, variable)
            if n_msg == 0:
                break
            else:  # pragma: debug
                self.verbose_debug("Draining %d %s messages.",
                                   n_msg, variable)
                self.sleep()
        self.stop_timeout(key_suffix='.drain_messages')
        self.debug('Done draining')

    def purge(self):
        r"""Purge all messages from the comm."""
        self._n_sent = 0
        self._n_recv = 0
        self._last_send = None
        self._last_recv = None

    # Send/recv dictionary of fields
    def send_dict(self, args_dict, field_order=None, **kwargs):
        r"""Send a message with fields specified in the input dictionary.

        Args:
            args_dict (dict): Dictionary with fields specifying output fields.
            field_order (list, optional): List of fields in the order they
                should be passed to send. If not provided, the fields from
                the serializer are used. If the serializer dosn't have
                field names an error will be raised.
            **kwargs: Additiona keyword arguments are passed to send.

        Returns:
            bool: Success/failure of send.

        Raises:
            RuntimeError: If the field order can not be determined.

        """
        if field_order is None:
            if self.serializer.field_names is not None:
                field_order = [
                    backwards.bytes2unicode(n) for n in self.serializer.field_names]
            elif len(args_dict) <= 1:
                field_order = [k for k in args_dict.keys()]
            else:  # pragma: debug
                raise RuntimeError("Could not determine the field order.")
        as_array = True
        for v in args_dict.values():
            if not isinstance(v, np.ndarray):
                as_array = False
                break
        if as_array:
            args = (serialize.dict2numpy(args_dict, order=field_order), )
        else:
            args = tuple([args_dict[k] for k in field_order])
        return self.send(*args, **kwargs)

    def recv_dict(self, *args, **kwargs):
        r"""Return a received message as a dictionary of fields. If there are
        not any fields specified, the fields will have the form 'f0', 'f1',
        'f2', ...

        Args:
            *args: Arguments are passed to recv.
            **kwargs: Keyword arguments are passed to recv.

        Returns:
            tuple(bool, dict): Success/failure of receive and a dictionar of
                message fields.

        Raises:

        """
        flag, msg = self.recv(*args, **kwargs)
        if flag and not self.is_eof(msg):
            if isinstance(msg, np.ndarray):
                msg_dict = serialize.numpy2dict(msg)
            elif isinstance(msg, pd.DataFrame):
                msg_dict = serialize.pandas2dict(msg)
            elif isinstance(msg, tuple):
                if self.serializer.field_names is None:  # pragma: debug
                    field_names = ['f%d' % i for i in range(len(msg))]
                else:
                    field_names = [
                        backwards.bytes2unicode(n) for n in self.serializer.field_names]
                msg_dict = {k: v for k, v in zip(field_names, msg)}
            else:
                msg_dict = {'f0': msg}
        else:
            msg_dict = msg
        return flag, msg_dict

    # SEND/RECV FIELDS
    # def recv_field(self, field, *args, **kwargs):
    #     r"""Receive an entry for a single field.

    #     Args:
    #         field (str): Name of the field that should be received.
    #         *args: All arguments are passed to recv method if there is not
    #             an existing entry for the requested field.
    #         **kwargs: All keyword arguments are passed to recv method if there
    #             is not an existing entry for the requested field.

    #     Returns:
    #         tuple (bool, obj): Success or failure of receive and received
    #             field entry.

    #     """
    #     flag = True
    #     field_msg = self.empty_msg
    #     if not self._field_backlog.get(field, []):
    #         flag, msg = self.recv_dict(*args, **kwargs)
    #         if self.is_eof(msg):
    #             for k in self.fields:
    #                 self._field_backlog.setdefault(k, [])
    #                 self._field_backlog[k].append(msg)
    #         elif not self.is_empty_recv(msg):
    #             for k, v in msg.items():
    #                 self._field_backlog.setdefault(k, [])
    #                 self._field_backlog.append(v)
    #     if self._field_backlog.get(field, []):
    #         field_msg = self._field_backlog[field].pop(0)
    #     return flag, field_msg

    # ALIASES
    def send_line(self, *args, **kwargs):
        r"""Alias for send."""
        return self.send(*args, **kwargs)

    def recv_line(self, *args, **kwargs):
        r"""Alias for recv."""
        return self.recv(*args, **kwargs)

    def send_row(self, *args, **kwargs):
        r"""Alias for send."""
        return self.send(*args, **kwargs)

    def recv_row(self, *args, **kwargs):
        r"""Alias for recv."""
        return self.recv(*args, **kwargs)

    def send_array(self, *args, **kwargs):
        r"""Alias for send."""
        return self.send(*args, **kwargs)

    def recv_array(self, *args, **kwargs):
        r"""Alias for recv."""
        return self.recv(*args, **kwargs)
