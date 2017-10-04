# from logging import debug, error, exception
import os
from cis_interface import backwards
from cis_interface.tools import PSI_MSG_MAX  # , PSI_MSG_EOF


def default_serialize(x):
    return backwards.unicode2bytes(x)


def default_deserialize(x):
    return x


class CommBase(object):
    r"""Class for handling I/O.

    Args:
        name (str): The environment variable where communication addres is
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
        dont_open (bool, optional): If True, the connection will not be opened.
            Defaults to False.

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
                 deserialize=None, serialize=None, dont_open=False):
        self.name = name
        if address is None:
            if self.name not in os.environ:
                raise Exception('Cannot see %s in env.' % self.name)
            self.address = os.environ[self.name]
        else:
            self.address = address
        self.direction = direction
        if deserialize is None:
            deserialize = default_deserialize
        if serialize is None:
            serialize = default_serialize
        self.meth_deserialize = deserialize
        self.meth_serialize = serialize
        if not dont_open:
            self.open()

    @classmethod
    def new_comm(cls, *args, **kwargs):
        r"""Initialize communication with new queue."""
        kwargs['address'] = 'address'
        return cls(*args, **kwargs)

    def opp_comm_kwargs(self):
        r"""Get keyword arguments to initialize communication with opposite
        comm object.

        Returns:
            dict: Keyword arguments for opposite comm object.

        """
        kwargs = {}
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
    def _send(self, msg):
        r"""Raw send. Should be overridden by inheriting class."""
        return False

    def _send_nolimit(self, msg):
        r"""Raw send_nolimit. Should be overridden by inheriting class."""
        return self._send(msg)

    def send(self, msg):
        r"""Send a message shorter than PSI_MSG_MAX.

        Args:
            msg (obj): Message to be sent that can be parsed by meth_serialize.

        Returns:
            bool: Success or failure of send.

        """
        if self.is_closed:
            return False
        msg_s = self.serialize(msg)
        return self._send(msg_s)

    def send_nolimit(self, msg):
        r"""Send a message larger than PSI_MSG_MAX.

        Args:
            msg (obj): Message to be sent that can be parsed by meth_serialize.

        Returns:
            bool: Success or failure of send.

        """
        if self.is_closed:
            return False
        msg_s = self.serialize(msg)
        return self._send_nolimit(msg_s)

    # RECV METHODS
    def _recv(self):
        r"""Raw recv. Should be overridden by inheriting class."""
        return (False, None)

    def _recv_nolimit(self):
        r"""Raw send_nolimit. Should be overridden by inheriting class."""
        return self._recv()
        
    def recv(self):
        r"""Receive a message shorter than PSI_MSG_MAX.

        Returns:
            tuple (bool, obj): Success or failure of receive and received
                message.

        """
        if self.is_closed:
            return (False, None)
        flag, s_msg = self._recv()
        if not flag:
            return (False, None)
        return (True, self.deserialize(s_msg))

    def recv_nolimit(self):
        r"""Receive a message larger than PSI_MSG_MAX.

        Returns:
            tuple (bool, obj): Success or failure of receive and received
                message.

        """
        if self.is_closed:
            return (False, None)
        flag, s_msg = self._recv_nolimit()
        if not flag:
            return (False, None)
        return (True, self.deserialize(s_msg))
