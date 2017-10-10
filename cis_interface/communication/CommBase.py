import os
from cis_interface import backwards
from cis_interface.tools import CisClass, PSI_MSG_MAX, PSI_MSG_EOF
from cis_interface.serialize.DefaultSerialize import DefaultSerialize
from cis_interface.serialize.DefaultDeserialize import DefaultDeserialize

    
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

    Raises:
        Exception: If there is not an environment variable with the specified
            name.

    """
    def __init__(self, name, address=None, direction='send',
                 deserialize=None, serialize=None, format_str=None,
                 dont_open=False, **kwargs):
        super(CommBase, self).__init__(name, **kwargs)
        self.name = name
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
        if not dont_open:
            self.open()

    @property
    def comm_count(self):
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
    def new_comm(cls, *args, **kwargs):
        r"""Initialize communication with new queue."""
        args, kwargs = cls.new_comm_kwargs(*args, **kwargs)
        return cls(*args, **kwargs)

    def opp_comm_kwargs(self):
        r"""Get keyword arguments to initialize communication with opposite
        comm object.

        Returns:
            dict: Keyword arguments for opposite comm object.

        """
        kwargs = {'comm': self.comm_class}
        kwargs['address'] = self.address
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
        pass

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
        return PSI_MSG_EOF

    def chunk_message(self, msg):
        r"""Yield chunks of message of size PSI_MSG_MAX.

        Args:
            msg (str, bytes): Raw message bytes to be chunked.

        Returns:
            str: Chunks of message.

        """
        prev = 0
        while prev < len(msg):
            next = min(prev + PSI_MSG_MAX, len(msg))
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

    # SEND METHODS
    def _send(self, msg, *args, **kwargs):
        r"""Raw send. Should be overridden by inheriting class."""
        return False

    def _send_nolimit(self, msg, *args, **kwargs):
        r"""Raw send_nolimit. Should be overridden by inheriting class."""
        return self._send(msg, *args, **kwargs)

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
        if msg == self.eof_msg:
            flag = self.on_send_eof()
            msg_s = backwards.unicode2bytes(msg)
        else:
            flag = True
            msg_s = self.serialize(msg)
        return flag, msg_s

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
        r"""Send the EOF message as a large message.
        
        Args:
            *args: All arguments are passed to comm send_nolimit.
            **kwargs: All keywords arguments are passed to comm send_nolimit.

        Returns:
            bool: Success or failure of send.

        """
        return self.send_nolimit(self.eof_msg, *args, **kwargs)
        
    def send(self, *args, **kwargs):
        r"""Send a message shorter than PSI_MSG_MAX.

        Args:
            *args: All arguments are assumed to be part of the message.
            **kwargs: All keywords arguments are passed to comm _send method.

        Returns:
            bool: Success or failure of send.

        """
        flag, msg_s = self.on_send(args)
        if not flag:
            return False
        try:
            self.debug('.send(): %d bytes', len(msg_s))
            ret = self._send(msg_s, **kwargs)
            self.debug('.send(): %d bytes sent', len(msg_s))
        except:
            self.exception('.send(): Failed to send.')
            return False
        return ret

    def send_nolimit(self, *args, **kwargs):
        r"""Send a message larger than PSI_MSG_MAX.

        Args:
            *args: All arguments assumed to be part of the message.
            **kwargs: All keywords arguments are passed to comm _send_nolimit
                method.

        Returns:
            bool: Success or failure of send.

        """
        flag, msg_s = self.on_send(args)
        if not flag:
            return False
        try:
            self.debug('.send_nolimit(): %d bytes', len(msg_s))
            ret = self._send_nolimit(msg_s, **kwargs)
            self.debug('.send_nolimit(): %d bytes sent', len(msg_s))
        except:
            self.exception('.send_nolimit(): Failed to send.')
            return False
        return ret

    # RECV METHODS
    def _recv(self, *args, **kwargs):
        r"""Raw recv. Should be overridden by inheriting class."""
        return (False, None)

    def _recv_nolimit(self, *args, **kwargs):
        r"""Raw send_nolimit. Should be overridden by inheriting class."""
        return self._recv(*args, **kwargs)

    def on_recv_eof(self):
        r"""Actions to perform when EOF received.

        Returns:
            bool: Flag that should be returned for EOF.

        """
        self.close()
        return False
    
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
        r"""Receive a message shorter than PSI_MSG_MAX.

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
        try:
            flag, s_msg = self._recv(*args, **kwargs)
            self.debug('.recv(): %d bytes received', len(s_msg))
        except:
            self.exception('.recv(): Failed to recv.')
            return (False, None)
        if flag:
            flag, msg = self.on_recv(s_msg)
        else:
            msg = None
        return (flag, msg)

    def recv_nolimit(self, *args, **kwargs):
        r"""Receive a message larger than PSI_MSG_MAX.

        Args:
            *args: All arguments are passed to comm _recv_nolimit method.
            **kwargs: All keywords arguments are passed to comm _recv_nolimit
                method.

        Returns:
            tuple (bool, obj): Success or failure of receive and received
                message.

        """
        if self.is_closed:
            self.debug('.recv_nolimit(): comm closed.')
            return (False, None)
        try:
            flag, s_msg = self._recv_nolimit(*args, **kwargs)
            self.debug('.recv_nolimit(): %d bytes received', len(s_msg))
        except:
            self.exception('.recv_nolimit(): Failed to recv.')
            return (False, None)
        if flag:
            flag, msg = self.on_recv(s_msg)
        else:
            msg = None
        return (flag, msg)
