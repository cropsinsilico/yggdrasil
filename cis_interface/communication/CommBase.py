import os
import uuid
import atexit
import threading
from cis_interface import backwards, tools
from cis_interface.tools import CisClass, get_CIS_MSG_MAX, CIS_MSG_EOF
from cis_interface.serialize.DefaultSerialize import DefaultSerialize
from cis_interface.serialize.DefaultDeserialize import DefaultDeserialize
from cis_interface.communication import (
    new_comm, get_comm, get_comm_class)


CIS_MSG_HEAD = backwards.unicode2bytes('CIS_MSG_HEAD')
HEAD_VAL_SEP = backwards.unicode2bytes(':CIS:')
HEAD_KEY_SEP = backwards.unicode2bytes(',')

    
class CommBase(CisClass):
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
        deserialize (obj, optional): Callable object that takes bytes as input
            and returnes deserialized version. This will be used to process
            received messages. Defaults to None and raw bytes will be returned
            by recv.
        serialize (obj, optional): Callable object that takes any object as
            input and returns a serialized set of bytes. This will be used
            to encode sent messages. Defaults to None and send will assume
            that all messages are raw bytes.
        format_str (str, optional): If provided and deserialize and/or serialize
            are not provided, this string will be used to format/parse messages
            that are sent/received. Defaults to None.
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
        comm (str, optional): The comm that should be created. This only serves
            as a check that the correct class is being created. Defaults to None.
        **kwargs: Additional keywords arguments are passed to parent class.

    Attributes:
        name (str): The environment variable where communication address is
            stored.
        address (str): Communication info.
        direction (str): The direction that messages should flow through the
            connection.
        meth_deserialize (obj): Callable object that takes bytes as input
            and returnes deserialized version. This will be used to process
            received messages.
        meth_serialize (obj): Callable object that takes any object as
            input and returns a serialized set of bytes. This will be used
            to encode sent messages.
        is_interface (bool): True if this comm is a Python interface binding.
        recv_timeout (float): Time that should be waited for an incoming
            message before returning None.
        close_on_eof_recv (bool): If True, the comm will be closed when it
            receives an end-of-file messages. Otherwise, it will remain open.
        single_use (bool): If True, the comm will only be used to send/recv a
            single message.
        is_client (bool): If True, the comm is one of many potential clients
            that will be sending messages to one or more servers.
        is_response_client (bool): If True, the comm is a client-side response
            comm.
        is_server (bool): If True, the commis one of many potential servers
            that will be receiving messages from one or more clients.
        is_response_server (bool): If True, the comm is a server-side response
            comm.

    Raises:
        RuntimeError: If the comm class is not installed.
        RuntimeError: If there is not an environment variable with the specified
            name.
        ValueError: If directions is not 'send' or 'recv'.

    """
    def __init__(self, name, address=None, direction='send',
                 deserialize=None, serialize=None, format_str=None,
                 dont_open=False, is_interface=False,
                 recv_timeout=0.0, close_on_eof_recv=True,
                 single_use=False, reverse_names=False, no_suffix=False,
                 is_client=False, is_response_client=False,
                 is_server=False, is_response_server=False,
                 comm=None, **kwargs):
        if comm is not None:
            assert(comm == self.comm_class)
        super(CommBase, self).__init__(name, **kwargs)
        if not self.__class__.is_installed():
            raise RuntimeError("Comm class %s not installed" % self.__class__)
        suffix = self.__class__._determine_suffix(
            no_suffix=no_suffix, reverse_names=reverse_names, direction=direction)
        self.name_base = name
        self.suffix = suffix
        self.name = name + suffix
        if address is None:
            if self.name not in os.environ:
                raise RuntimeError('Cannot see %s in env.' % self.name)
            self.address = os.environ[self.name]
        else:
            self.address = address
        self.direction = direction
        self.format_str = format_str
        if deserialize is None:
            deserialize = DefaultDeserialize(format_str=self.format_str)
        if serialize is None:
            serialize = DefaultSerialize(format_str=self.format_str)
        self.meth_deserialize = deserialize
        self.meth_serialize = serialize
        self.is_client = is_client
        self.is_response_client = is_response_client
        self.is_response_server = is_response_server
        self.is_server = is_server
        self.is_interface = is_interface
        self.recv_timeout = recv_timeout
        self.close_on_eof_recv = close_on_eof_recv
        self._last_header = None
        self._work_comms = {}
        self.single_use = single_use
        self._used = False
        self._first_send_done = False
        self._n_sent = 0
        self._n_recv = 0
        self._last_send = None
        self._last_recv = None
        self._timeout_drain = self.timeout
        if not dont_open:
            self.open()
        self._closing_event = threading.Event()
        self._closing_thread = tools.CisThread(target=self.linger_close)
        self._eof_sent = threading.Event()
        if self.is_interface:
            atexit.register(self.atexit)

    @classmethod
    def _determine_suffix(cls, no_suffix=False, reverse_names=False,
                          direction='send', **kwargs):
        r"""Determine the suffix that should be used for the comm name."""
        if direction not in ['send', 'recv']:
            raise ValueError("Unrecognized message direction: %s" % direction)
        if no_suffix:
            suffix = ''
        else:
            if ((((direction == 'send') and (not reverse_names)) or
                 ((direction == 'recv') and reverse_names))):
                suffix = '_OUT'
            else:
                suffix = '_IN'
        return suffix
    
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

    @classmethod
    def comm_count(cls):
        r"""int: Number of communication connections."""
        return 0

    @property
    def comm_class(self):
        r"""str: Name of communication class."""
        return str(self.__class__).split("'")[1].split(".")[-1]

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
        kwargs['serialize'] = self.meth_serialize
        kwargs['deserialize'] = self.meth_deserialize
        if self.direction == 'send':
            kwargs['direction'] = 'recv'
        else:
            kwargs['direction'] = 'send'
        return kwargs

    def open(self):
        r"""Open the connection."""
        pass

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
            if linger and self.is_open:
                self.drain_messages()
            else:
                self._closing_thread.set_terminated_flag()
        self._close(linger=linger)
        if not skip_base:
            self.debug("Cleaning up %d work comms", len(self._work_comms))
            keys = [k for k in self._work_comms.keys()]
            for c in keys:
                self.remove_work_comm(c, linger=linger)
            self.debug("Finished cleaning up work comms")

    def close_on_empty(self, no_wait=False):
        r"""In a new thread, close the comm when it is empty."""
        with self._closing_thread.lock:
            if (((not self._closing_thread.was_started) and
                 (not self._closing_thread.was_terminated))):
                self._closing_thread.start()
        if self._closing_thread.was_started and (not no_wait):
            self._closing_thread.wait(key=str(uuid.uuid4()))

    def linger_close(self):
        r"""Wait for messages to drain, then close."""
        self.close(linger=True)

    def background_atexit(self):
        r"""Close operations in background."""
        self.atexit(no_wait=True)

    def atexit(self, no_wait=False):
        r"""Close operations."""
        if self.is_interface and (self.direction == 'send'):
            self.interface_close(no_wait=no_wait)
        else:
            self.close()

    def interface_close(self, no_wait=False):
        r"""Close operations for interface send comms."""
        self.send_eof()
        self.linger_close()

    @property
    def is_open(self):
        r"""bool: True if the connection is open."""
        return False

    @property
    def is_closed(self):
        r"""bool: True if the connection is closed."""
        return (not self.is_open)

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

    def serialize(self, msg):
        r"""Serialize a message by turning it to bytes using meth_serialize.

        Args:
            msg (obj): Message to be serialized that can be parsed by
                meth_serialize.

        Returns:
            bytes, str: Serialized message.

        Raises:
            TypeError: If meth_serialize does not return bytes type.

        """
        msg_s = self.meth_serialize(msg)
        if not isinstance(msg_s, backwards.bytes_type):  # pragma: debug
            raise TypeError("Serialize method did not yield bytes type.")
        return msg_s

    def deserialize(self, msg):
        r"""Deserialize message by passing it to meth_deserialize.

        Args:
            msg (bytes, str): Message to be deserialized.

        Returns:
            obj: Deserialized message.

        Raises:
            TypeError: If msg is not bytes type.

        """
        if not isinstance(msg, backwards.bytes_type):  # pragma: debug
            raise TypeError("Deserialize method expects bytes type.")
        return self.meth_deserialize(msg)

    # TEMP COMMS
    @property
    def get_work_comm_kwargs(self):
        r"""dict: Keyword arguments for an existing work comm."""
        return dict(comm=self.comm_class, direction='recv',
                    recv_timeout=self.recv_timeout,
                    single_use=True)

    @property
    def create_work_comm_kwargs(self):
        r"""dict: Keyword arguments for a new work comm."""
        return dict(comm=self.comm_class, direction='send',
                    recv_timeout=self.recv_timeout,
                    single_use=True)

    def get_work_comm(self, header, work_comm_name=None, **kwargs):
        r"""Get temporary work comm, creating as necessary.

        Args:
            header (dict): Information that will be sent in the message header
                to the work comm.
            work_comm_name (str, optional): Name that should be used for the
                work comm. If not provided, one is created from the header id
                and the comm class.
            **kwargs: Additional keyword arguments are passed to get_comm.

        Returns:
            Comm: Work comm.

        """
        c = self._work_comms.get(header['id'], None)
        if c is not None:
            return c
        kws = self.get_work_comm_kwargs
        kws.update(**kwargs)
        if work_comm_name is None:
            cls = kws.get("comm", tools.get_default_comm())
            work_comm_name = 'temp_%s_%s.%s' % (
                cls, kws['direction'], header['id'])
        c = get_comm(work_comm_name, address=header['address'], **kws)
        self.add_work_comm(header['id'], c)
        return c

    def create_work_comm(self, header, work_comm_name=None, **kwargs):
        r"""Create a temporary work comm.

        Args:
            header (dict): Info that should be sent with message.
            work_comm_name (str, optional): Name that should be used for the
                work comm. If not provided, one is created from the header id
                and the comm class.
            **kwargs: Keyword arguments for new_comm that should override
                work_comm_kwargs.

        Returns:
            Comm: Work comm.

        """
        kws = self.create_work_comm_kwargs
        kws.update(**kwargs)
        if work_comm_name is None:
            cls = kws.get("comm", tools.get_default_comm())
            work_comm_name = 'temp_%s_%s.%s' % (
                cls, kws['direction'], header['id'])
        c = new_comm(work_comm_name, **kws)
        self.add_work_comm(header['id'], c)
        return c

    def add_work_comm(self, key, comm):
        r"""Add work comm to dict.

        Args:
            key (str): Key that should be used to log the comm.
            comm (Comm): Comm that should be added.

        Raises:
            KeyError: If there is already a comm associated with the key.

        """
        if key in self._work_comms:
            raise KeyError("Comm already registered with key %s." % key)
        self._work_comms[key] = comm

    def remove_work_comm(self, key, dont_close=False, linger=False):
        r"""Close and remove a work comm.

        Args:
            key (str): Key of comm that should be removed.
            dont_close (bool, optional): If True, the comm will be removed
                from the list, but it won't be closed. Defaults to False.
            linger (bool, optional): If True, drain messages before closing the
                comm. Defaults to False.

        """
        if key not in self._work_comms:
            return
        if not dont_close:
            c = self._work_comms.pop(key)
            c.close(linger=linger)

    # HEADER
    def get_header(self, msg, no_address=False, **kwargs):
        r"""Create a dictionary of message properties.

        Args:
            msg (str): Message to get header for.
            no_address (bool, optional): If True, an address won't be added to
                the header and a work comm won't be created. Defaults to False.
            **kwargs: Additional keyword args are used to initialized the
                header.

        Returns:
           dict: Properties that should be encoded in a messaged header.

        """
        out = dict(**kwargs)
        out['size'] = len(msg)
        out.setdefault('id', str(uuid.uuid4()))
        if not no_address:
            c = self.create_work_comm(out)
            out['address'] = c.address
        return out

    def format_header(self, header_info):
        r"""Format header info to form a string that should prepend a message.

        Args:
            header_info (dict): Properties that should be incldued in the header.

        Returns:
            str: Message with header in front.

        """
        header = backwards.bytes2unicode(CIS_MSG_HEAD)
        header += backwards.bytes2unicode(HEAD_KEY_SEP).join(
            ['%s%s%s' % (backwards.bytes2unicode(k),
                         backwards.bytes2unicode(HEAD_VAL_SEP),
                         backwards.bytes2unicode(str(v))) for k, v in
             header_info.items()])
        header += backwards.bytes2unicode(CIS_MSG_HEAD)
        return backwards.unicode2bytes(header)

    def parse_header(self, msg):
        r"""Extract header info from a message.

        Args:
            msg (str): Message to extract header from.

        Returns:
            dict: Message properties.

        """
        if CIS_MSG_HEAD not in msg:
            out = dict(body=msg, size=len(msg))
            return out
        _, header, body = msg.split(CIS_MSG_HEAD)
        out = dict(body=body)
        for x in header.split(HEAD_KEY_SEP):
            k, v = x.split(HEAD_VAL_SEP)
            out[backwards.bytes2unicode(k)] = backwards.bytes2unicode(v)
        return out

    # SEND METHODS
    def _safe_send(self, *args, **kwargs):
        r"""Send message checking if is 1st message and then waiting."""
        if not self._first_send_done:
            out = self._send_1st(*args, **kwargs)
        else:
            out = self._send(*args, **kwargs)
        if out:
            self._n_sent += 1
            self._last_send = backwards.clock_time()
        return out
    
    def _send_1st(self, *args, **kwargs):
        r"""Send first message until it succeeds."""
        T = self.start_timeout()
        flag = self._send(*args, **kwargs)
        self.suppress_special_debug = True
        while (not T.is_out) and (self.is_open) and (not flag):
            flag = self._send(*args, **kwargs)
            if flag or (self.is_closed):
                break
            self.sleep()
        self.stop_timeout()
        self.suppress_special_debug = False
        self._first_send_done = True
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

    def _send_multipart_worker(self, msg, header, **kwargs):
        r"""Send multipart message to the worker comm identified.

        Args:
            msg (str): Message to be sent.
            header (dict): Message info including work comm address.

        Returns:
            bool: Success or failure of sending the message.

        """
        workcomm = self.get_work_comm(header)
        ret = workcomm._send_multipart(msg, **kwargs)
        self.remove_work_comm(header['id'], dont_close=True)
        return ret
            
    def on_send_eof(self):
        r"""Actions to perform when EOF being sent.

        Returns:
            bool: True if EOF message should be sent, False otherwise.

        """
        return True

    def on_send(self, msg):
        r"""Process message to be sent including handling serializing
        message and handling EOF.

        Args:
            msg (obj): Message to be sent

        Returns:
            tuple (bool, str): Truth of if message should be sent and raw bytes
                message to send.

        """
        if self.is_closed:
            self.debug('Comm closed')
            return False, self.empty_msg
        if len(msg) == 1:
            msg = msg[0]
        if isinstance(msg, backwards.bytes_type) and msg == self.eof_msg:
            flag = self.on_send_eof()
            msg_s = backwards.unicode2bytes(msg)
        else:
            flag = True
            msg_s = self.serialize(msg)
        return flag, msg_s

    def send(self, *args, **kwargs):
        r"""Send a message.

        Args:
            *args: All arguments are assumed to be part of the message.
            **kwargs: All keywords arguments are passed to comm _send method.

        Returns:
            bool: Success or failure of send.

        """
        flag, msg_s = self.on_send(args)
        if not flag:
            return False
        if self.single_use and self._used:
            raise RuntimeError("This comm is single use and it was already used.")
        try:
            self.special_debug('Sending %d bytes', len(msg_s))
            self._used = True
            ret = self.send_multipart(msg_s, **kwargs)
            if ret:
                self.debug('Sent %d bytes', len(msg_s))
            else:
                self.special_debug('Failed to send %d bytes', len(msg_s))
        except BaseException:
            self.exception('.send(): Failed to send.')
            return False
        return ret

    def send_multipart(self, msg, send_header=False, header_kwargs=None,
                       **kwargs):
        r"""Send a multipart message. If the message is smaller than maxMsgSize,
        it is sent using _send, otherwise it is sent to a worker comm using
        _send_multipart.

        Args:
            msg (bytes): Message to be sent.
            send_header (bool, optional): If True, the message will be sent as
                multipart with header even if the message is smaller than
                maxMsgSize. Defaults to False.
            header_kwargs (dict, optional): Keyword arguments that should be
                added to the header.
            **kwargs: Additional keyword arguments are passed to _send or
                _send_multipart.

        Returns:
            bool: Success or failure of send.

        """
        if (not send_header) and ((len(msg) < self.maxMsgSize) or
                                  (self.maxMsgSize == 0)):
            if self.is_closed:  # pragma: debug
                self.error("Connection closed.")
                return False
            ret = self._safe_send(msg, **kwargs)
        else:
            if header_kwargs is None:
                header_kwargs = dict()
            header = self.get_header(msg, no_address=True, **header_kwargs)
            header_msg = self.format_header(header)
            if ((((len(header_msg) + len(msg)) < self.maxMsgSize) or
                 (self.maxMsgSize == 0))):
                ret = self._safe_send(header_msg + msg)
            else:
                header = self.get_header(msg, **header_kwargs)
                header_msg = self.format_header(header)
                ret = self._safe_send(header_msg)
                if not ret:  # pragma: debug
                    self.special_debug("Sending message header failed.")
                    return ret
                ret = self._send_multipart_worker(msg, header, **kwargs)
        return ret
        
    # def send_header(self, header, **kwargs):
    #     r"""Send header message.

    #     Args:
    #         header (dict): Header info that should be sent.
    #         **kwargs: Additional keyword arguments are passed to _send method.

    #     Returns:
    #         bool: Success or failure of send.

    #     """
    #     header_msg = self.format_header(header)
    #     if self.is_closed:  # pragma: debug
    #         self.error("Connection closed.")
    #         return False
    #     out = self._safe_send(header_msg, **kwargs)
    #     return out

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
        if not self._eof_sent.is_set():
            self._eof_sent.set()
            return self.send(self.eof_msg, *args, **kwargs)
        return False
        
    def send_nolimit_eof(self, *args, **kwargs):
        r"""Alias for send_eof."""
        return self.send_eof(*args, **kwargs)

    # RECV METHODS
    def _safe_recv(self, *args, **kwargs):
        r"""Save receive that does things for all comm classes."""
        out = self._recv(*args, **kwargs)
        if out[0]:
            self._n_recv += 1
            self._last_recv = backwards.clock_time()
        return out

    def _recv(self, *args, **kwargs):
        r"""Raw recv. Should be overridden by inheriting class."""
        raise NotImplementedError("_recv method needs implemented.")

    def _recv_multipart(self, leng_exp, **kwargs):
        r"""Receive a message larger than CIS_MSG_MAX that is sent in multiple
        parts.

        Args:
            leng_exp (int): Size of message expected.
            **kwargs: All keyword arguments are passed to _recv.

        Returns:
            tuple (bool, str): The success or failure of receiving a message
                and the complete message received.

        """
        data = self.empty_msg
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
            **kwargs: All keyword arguments are passed to _recv.

        Returns:
            tuple (bool, str): The success or failure of receiving a message
                and the complete message received.

        """
        workcomm = self.get_work_comm(info)
        leng_exp = int(float(info['size']))
        out = workcomm._recv_multipart(leng_exp, **kwargs)
        self.remove_work_comm(info['id'])
        return out
        
    def on_recv_eof(self):
        r"""Actions to perform when EOF received.

        Returns:
            bool: Flag that should be returned for EOF.

        """
        if self.close_on_eof_recv:
            self.close()
            return False
        else:
            return True
    
    def on_recv(self, s_msg, *args, **kwargs):
        r"""Process raw received message including handling deserializing
        message and handling EOF.

        Args:
            s_msg (bytes, str): Raw bytes message.

        Returns:
            tuple (bool, str): Success or failure and processed message.

        """
        if s_msg == self.eof_msg:
            flag = self.on_recv_eof()
            msg = s_msg
            self._used = True
        else:
            flag = True
            msg = self.deserialize(s_msg)
            self._used = True
        return flag, msg

    def recv(self, *args, **kwargs):
        r"""Receive a message shorter than CIS_MSG_MAX.

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
            flag, s_msg = self.recv_multipart(*args, **kwargs)
            if flag and len(s_msg) > 0:
                self.debug('%d bytes received', len(s_msg))
        except Exception:
            self.exception('Failed to recv.')
            return (False, None)
        if flag:
            flag, msg = self.on_recv(s_msg, *args, **kwargs)
        else:
            msg = None
        if self.single_use and self._used:
            self.close()
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
        flag, info = self.recv_header(*args, **kwargs)
        if not flag or info['size'] == 0:
            if not flag:
                self.debug("Failed to receive message header.")
            return flag, info['body']
        self._last_header = info
        if len(info['body']) == int(info['size']):
            return True, info['body']
        out = self._recv_multipart_worker(info, **kwargs)
        self.remove_work_comm(info['id'])
        return out
        
    def recv_header(self, *args, **kwargs):
        r"""Receive header message.

        Args:
            *args: All arguments are passed to comm _recv method.
            **kwargs: All keywords arguments are passed to comm _recv method.

        Returns:
            tuple (bool, dict): Success or failure of receive and received
                header information.

        """
        flag, s_msg = self._safe_recv(*args, **kwargs)
        if not flag:
            return flag, dict(body=s_msg, size=0)
        info = self.parse_header(s_msg)
        return True, info

    def recv_nolimit(self, *args, **kwargs):
        r"""Alias for recv."""
        return self.recv(*args, **kwargs)

    def drain_messages(self, direction=None, timeout=None):
        r"""Sleep while waiting for messages to be drained."""
        if direction is None:
            direction = self.direction
        if direction == 'send':
            self.drain_messages_send(timeout=timeout)
        else:
            self.drain_messages_recv(timeout=timeout)

    def drain_messages_recv(self, timeout=None):
        r"""Sleep while waiting for recv messages to be drained."""
        if timeout is None:
            timeout = self._timeout_drain
        Tout = self.start_timeout(timeout)
        while (not Tout.is_out) and (self.n_msg_recv_drain > 0) and self.is_open:
            self.verbose_debug("Draining recv messages.")
            self.sleep()
        self.stop_timeout()

    def drain_messages_send(self, timeout=None):
        r"""Sleep while waiting for send messages to be drained."""
        if timeout is None:
            timeout = self._timeout_drain
        Tout = self.start_timeout(timeout)
        while (not Tout.is_out) and (self.n_msg_send_drain > 0) and self.is_open:
            self.verbose_debug("Draining send messages.")
            self.sleep()
        self.stop_timeout()

    def purge(self):
        r"""Purge all messages from the comm."""
        self._n_sent = 0
        self._n_recv = 0
        self._last_send = None
        self._last_recv = None

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
