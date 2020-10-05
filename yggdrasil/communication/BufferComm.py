from yggdrasil import multitasking
from yggdrasil.communication import CommBase


class LockedBuffer(multitasking.Queue):
    r"""Buffer intended to be shared between threads/processes."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('task_method', 'process')
        super(LockedBuffer, self).__init__(*args, **kwargs)
        self._closed = self.context.Event()

    @property
    def closed(self):
        r"""bool: True if the queue is closed, False otherwise."""
        if hasattr(self, '_closed'):
            return self._closed.is_set()
        return True  # pragma: debug

    def close(self, join=False):
        r"""Close the buffer."""
        # with self.lock:
        self.disconnect()

    def disconnect(self):
        if hasattr(self, '_closed'):
            self._closed.set()
            self._closed.disconnect()
        super(LockedBuffer, self).disconnect()
        
    def __len__(self):
        if self.closed:  # pragma: debug
            return 0
        return int(not self.empty())

    def append(self, x):
        r"""Add an element to the queue."""
        self.put_nowait(x)

    def pop(self, index=None, default=None):
        r"""Remove the first element from the queue."""
        assert(index == 0)
        # with self.lock:
        if (len(self) == 0) and (default is not None):
            return default
        return self.get()

    def clear(self):
        r"""Remove all elements from the queue."""
        # with self.lock:
        while not self.empty():
            self.get()


class BufferComm(CommBase.CommBase):
    r"""Class for handling I/O to an in-memory buffer.

    Args:
        name (str): The name of the message queue.
        address (LockedBuffer, optional): Existing buffer that should be
            used. If not provided, a new buffer is created.
        buffer_task_method (str, optional): Type of tasks that buffer
            will be used to share information between. Defaults to 'thread'.
        **kwargs: Additional keyword arguments are passed to CommBase.
        
    Attributes:
        address (LockedBuffer): Buffer containing messages.
        buffer_task_method (str): Type of tasks that buffer will be
            used to share information between.
        
    """
    _commtype = 'buffer'
    no_serialization = True

    def __init__(self, *args, buffer_task_method="thread", **kwargs):
        self.buffer_task_method = buffer_task_method
        super(BufferComm, self).__init__(*args, **kwargs)

    @classmethod
    def is_installed(cls, language=None):
        r"""Determine if the necessary libraries are installed for this
        communication class.

        Args:
            language (str, optional): Specific language that should be checked
                for compatibility. Defaults to None and all languages supported
                on the current platform will be checked. If set to 'any', the
                result will be True if this comm is installed for any of the
                supported languages.

        Returns:
            bool: Is the comm installed.

        """
        if language == 'python':
            return True
        return False
        
    def bind(self):
        r"""Bind to address, getting random port as necessary."""
        super(BufferComm, self).bind()
        if not isinstance(self.address, LockedBuffer):
            if self.address == 'address':
                self.address = LockedBuffer(task_method=self.buffer_task_method)
            else:  # pragma: debug
                raise ValueError("Invalid address for a buffer: %s"
                                 % self.address)
        
    def serialize(self, args, **kwargs):
        r"""Serialize a message using the associated serializer."""
        return args
        
    def deserialize(self, args, **kwargs):
        r"""Deserialize a message using the associated deserializer."""
        return args, {}
    
    @property
    def is_open(self):
        r"""bool: True if the connection is open."""
        return (not self.address.closed)
        
    def _close(self, *args, **kwargs):
        r"""Close the connection."""
        self.address.close()
        
    @property
    def n_msg_recv(self):
        r"""int: Number of messages in the receive backlog."""
        return len(self.address)

    @property
    def n_msg_send(self):
        r"""int: Number of messages in the send backlog."""
        return len(self.address)

    @property
    def is_confirmed_send(self):
        r"""bool: True if all sent messages have been confirmed."""
        return (self.n_msg_send == 0)

    @property
    def is_confirmed_recv(self):
        r"""bool: True if all received messages have been confirmed."""
        return (self.n_msg_recv == 0)

    def _send(self, payload, **kwargs):
        r"""Send a message to the buffer.

        Args:
            payload (str): Message to send.

        Returns:
            bool: Success or failure of sending the message.

        """
        if self.direction == 'recv':  # pragma: debug
            self.error("Receiving buffer comm cannot send.")
            return False
        self.address.append(payload)
        return True

    def _recv(self, timeout=None):
        r"""Receive a message from the buffer.

        Args:
            timeout (float, optional): Time in seconds to wait for a message.
                Defaults to self.recv_timeout.

        Returns:
            tuple (bool, str): The success or failure of receiving a message
                and the message received.

        """
        if timeout is None:  # pragma: no cover
            timeout = self.recv_timeout
        if self.direction == 'send':  # pragma: debug
            self.error("Sending buffer comm cannot receive.")
            return (False, self.empty_bytes_msg)
        # Sleep until there is a message
        T = self.start_timeout(timeout, key_suffix='_recv')
        while (not T.is_out) and (not len(self.address)):
            self.sleep()
        self.stop_timeout(key_suffix='_recv')
        return (True, self.address.pop(0, self.empty_bytes_msg))

    def purge(self):
        r"""Purge all messages from the comm."""
        super(BufferComm, self).purge()
        self.address.clear()
