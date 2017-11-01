import os
import uuid
from cis_interface import backwards
from cis_interface.tools import CisClass, CIS_MSG_MAX, CIS_MSG_EOF
from cis_interface.serialize.DefaultSerialize import DefaultSerialize
from cis_interface.serialize.DefaultDeserialize import DefaultDeserialize
from cis_interface.communication import (
    new_comm, get_comm, get_comm_class, _default_comm)


CIS_MSG_HEAD = 'CIS_MSG_HEAD'
HEAD_VAL_SEP = ':CIS:'
HEAD_KEY_SEP = ','

    
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
        recv_timeout (float): Time that should be waited for an incoming
            message before returning None.
        close_on_eof_recv (bool): If True, the comm will be closed when it
            receives an end-of-file messages. Otherwise, it will remain open.
        single_use (bool): If True, the comm will only be used to send/recv a
            single message.

    Raises:
        Exception: If there is not an environment variable with the specified
            name.

    """
    def __init__(self, name, address=None, direction='send',
                 deserialize=None, serialize=None, format_str=None,
                 dont_open=False, recv_timeout=0.0, close_on_eof_recv=True,
                 single_use=False, reverse_names=False, no_suffix=False,
                 **kwargs):
        super(CommBase, self).__init__(name, **kwargs)
        if no_suffix:
            suffix = ''
        else:
            if ((((direction == 'send') and (not reverse_names)) or
                 ((direction == 'recv') and reverse_names))):
                suffix = '_OUT'
            else:
                suffix = '_IN'
        self.name = name + suffix
        if address is None:
            if self.name not in os.environ:
                raise Exception('Cannot see %s in env.' % self.name)
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
        self.recv_timeout = recv_timeout
        self.close_on_eof_recv = close_on_eof_recv
        self._last_header = None
        self._work_comms = {}
        self.single_use = single_use
        self._used = False
        if not dont_open:
            self.open()

    @property
    def maxMsgSize(self):
        r"""int: Maximum size of a single message that should be sent."""
        return CIS_MSG_MAX

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
        if name in os.environ:
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

    def close(self):
        r"""Close the connection."""
        for c in self._work_comms.keys():
            self.remove_work_comm(c)

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
        return 0

    @property
    def eof_msg(self):
        r"""str: Message indicating EOF."""
        return CIS_MSG_EOF

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
        if not isinstance(msg_s, backwards.bytes_type):
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
        if not isinstance(msg, backwards.bytes_type):
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

    def get_work_comm(self, header, **kwargs):
        r"""Get temporary work comm, creating as necessary.

        Args:
            header (dict): Information that will be sent in the message header
                to the work comm.
            **kwargs: Additional keyword arguments are passed to get_comm.

        Returns:
            Comm: Work comm.

        """
        c = self._work_comms.get(header['id'], None)
        if c is not None:
            return c
        kws = self.get_work_comm_kwargs
        kws.update(**kwargs)
        cls = kws.get("comm", _default_comm)
        c = get_comm('temp_recv_%s.%s' % (cls, header['id']),
                     address=header['address'],
                     **kws)
        self.add_work_comm(header['id'], c)
        return c

    def create_work_comm(self, header, **kwargs):
        r"""Create a temporary work comm.

        Args:
            header (dict): Info that should be sent with message.
            **kwargs: Keyword arguments for new_comm that should override
                work_comm_kwargs.

        Returns:
            Comm: Work comm.

        """
        kws = self.create_work_comm_kwargs
        kws.update(**kwargs)
        cls = kws.get("comm", _default_comm)
        c = new_comm('temp_send_%s.%s' % (cls, header['id']), **kws)
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

    def remove_work_comm(self, key, dont_close=False):
        r"""Close and remove a work comm.

        Args:
            key (str): Key of comm that should be removed.
            dont_close (bool, optional): If True, the comm will be removed
                from the list, but it won't be closed. Defaults to False.

        """
        if key not in self._work_comms:
            return
        if not dont_close:
            c = self._work_comms.pop(key)
            c.close()

    # HEADER
    def get_header(self, msg, **kwargs):
        r"""Create a dictionary of message properties.

        Args:
            msg (str): Message to get header for.
            **kwargs: Additional keyword args are used to initialized the
                header.

        Returns:
           dict: Properties that should be encoded in a messaged header.

        """
        out = dict(**kwargs)
        out['size'] = len(msg)
        out.setdefault('id', str(uuid.uuid4()))
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
        header = CIS_MSG_HEAD
        header += HEAD_KEY_SEP.join(
            ['%s%s%s' % (k, HEAD_VAL_SEP, v) for k, v in header_info.items()])
        header += CIS_MSG_HEAD
        return header

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
            out[k] = v
        return out

    # SEND METHODS
    def _send(self, msg, *args, **kwargs):
        r"""Raw send. Should be overridden by inheriting class."""
        return False

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
            ret = self._send(imsg)
            if not ret:  # pragma: debug
                self.debug(
                    ".send_multipart(): send interupted at %d of %d bytes.",
                    nsent, len(msg))
                break
            nsent += len(imsg)
            self.debug(".send_multipart(): %d of %d bytes sent",
                       nsent, len(msg))
        if ret and len(msg) > 0:
            self.debug(".send_multipart %d bytes completed", len(msg))
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
            self.debug('.on_send(): comm closed.')
            return False, ''
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
            self.debug('.send(): %d bytes', len(msg_s))
            ret = self.send_multipart(msg_s, **kwargs)
            self._used = True
            self.debug('.send(): %d bytes sent', len(msg_s))
        except Exception:
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
            ret = self._send(msg, **kwargs)
        else:
            if header_kwargs is None:
                header_kwargs = dict()
            header = self.get_header(msg, **header_kwargs)
            # if header_kwargs is not None:
            #     header.update(**header_kwargs)
            ret = self.send_header(header)
            if not ret:  # pragma: debug
                self.debug(".send_multipart: Sending message header failed.")
                return ret
            ret = self._send_multipart_worker(msg, header, **kwargs)
        return ret
        
    def send_header(self, header, **kwargs):
        r"""Send header message.

        Args:
            header (dict): Header info that should be sent.
            **kwargs: Additional keyword arguments are passed to _send method.

        Returns:
            bool: Success or failure of send.

        """
        header_msg = self.format_header(header)
        out = self._send(header_msg, **kwargs)
        return out

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
        
    def send_nolimit_eof(self, *args, **kwargs):
        r"""Alias for send_eof."""
        return self.send_eof(*args, **kwargs)

    # RECV METHODS
    def _recv(self, *args, **kwargs):
        r"""Raw recv. Should be overridden by inheriting class."""
        return (False, None)

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
        data = backwards.unicode2bytes('')
        ret = True
        while len(data) < leng_exp:
            payload = self._recv(**kwargs)
            if not payload[0]:  # pragma: debug
                self.debug(
                    ".recv_multipart(): read interupted at %d of %d bytes.",
                    len(data), leng_exp)
                ret = False
                break
            data = data + payload[1]
            if len(payload[1]) == 0:
                self.sleep()
        payload = (ret, data)
        self.debug(".recv_multipart(): read %d bytes", len(data))
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
        else:
            flag = True
            msg = self.deserialize(s_msg)
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
        if self.is_closed:
            self.debug('.recv(): comm closed.')
            return (False, None)
        if self.single_use and self._used:
            raise RuntimeError("This comm is single use and it was already used.")
        try:
            flag, s_msg = self.recv_multipart(*args, **kwargs)
            if flag and len(s_msg) > 0:
                self.debug('.recv(): %d bytes received', len(s_msg))
            self._used = True
        except Exception:
            self.exception('.recv(): Failed to recv.')
            return (False, None)
        if flag:
            flag, msg = self.on_recv(s_msg)
        else:
            msg = None
        if self.single_use:
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
                self.debug(".recv_multipart(): Failed to receive message header.")
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
        flag, s_msg = self._recv(*args, **kwargs)
        if not flag:
            return flag, dict(body=s_msg, size=0)
        info = self.parse_header(s_msg)
        return True, info

    def recv_nolimit(self, *args, **kwargs):
        r"""Alias for recv."""
        return self.recv(*args, **kwargs)

    def purge(self):
        r"""Purge all messages from the comm."""
        pass

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
