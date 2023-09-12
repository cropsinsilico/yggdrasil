import os
import copy
from yggdrasil.communication.FileComm import FileComm


class DedicatedFileBase(FileComm):
    r"""Base class for handling I/O via a dedicated library."""

    _mode_as_bytes = False
    _default_serializer = False
    _deprecated_drivers = []
    _stores_fd = False
    _requires_refresh = False

    def __init__(self, *args, **kwargs):
        self._external_fd = None
        kwargs['read_meth'] = 'read'
        self._last_size = 0
        self._last_file_size = 0
        return super(DedicatedFileBase, self).__init__(*args, **kwargs)

    @property
    def concats_as_str(self):
        r"""bool: True if concatenating file contents result in a
        valid file."""
        return False

    @property
    def is_open(self):
        r"""bool: True if the connection is open."""
        if self._stores_fd:
            return super(DedicatedFileBase, self).is_open
        return bool(self._external_fd)

    @property
    def requires_refresh(self):
        r"""bool: True if a refresh is necessary."""
        return (
            self.is_open
            and ((self._external_fd is None)
                 or (self.append
                     or (self._requires_refresh
                         and self._last_file_size < self.file_size))))
    
    def serialize(self, obj, **kwargs):
        r"""Don't serialize for dedicated comms since using a serializer
        is inefficient."""
        return obj

    def deserialize(self, msg, **kwargs):
        r"""Don't deserialize for dedicated comms since using a serializer
        is inefficient."""
        return msg, {}

    # Methods related to position in the file/series
    @property
    def file_size(self):
        r"""int: Current size of file."""
        out = 0
        if os.path.isfile(self.current_address):
            out = os.stat(self.current_address).st_size
        return out

    def file_tell(self):
        r"""int: Current position in the file."""
        return self._last_size
    
    def file_seek(self, pos, whence=os.SEEK_SET):
        r"""Move in the file to the specified position.

        Args:
            pos (int): Position (in bytes) to move file to.
            whence (int, optional): Flag indicating position that pos
                is relative to. 0 for the beginning of the file, 1 for
                from the current location, and 2 from the end of the
                file.

        """
        if self._stores_fd:
            super(DedicatedFileBase, self).file_seek(pos, whence)
        if whence == 0:
            self._last_size = pos
        elif whence == 1:  # pragma: no cover
            self._last_size = min(self.file_size, self._last_size + pos)
        elif whence == 2:
            self._last_size = self.file_size
        
    def file_flush(self):
        r"""Flush the file."""
        if self._stores_fd:
            super(DedicatedFileBase, self).file_flush()
            if self._external_fd is not None:
                self._external_fd.flush()
                self._external_fd.sync()

    def _file_open(self, address, mode, **kwargs):
        self._last_size = 0
        if ((((not os.path.isfile(address)) or (os.stat(address).st_size == 0))
             and (mode == 'r') and self._stores_fd)):
            # Cannot open an empty file for read
            return super(DedicatedFileBase, self)._file_open(address, mode)
        out = self._dedicated_open(address, mode, **kwargs)
        self._last_file_size = self.file_size
        return out

    def _file_close(self, **kwargs):
        if self._external_fd is not None:
            self._dedicated_close(**kwargs)
        super(DedicatedFileBase, self)._file_close()

    def _file_refresh(self):
        prev_pos = self.file_tell()
        self._file_close()
        self._fd = self._file_open(self.current_address,
                                   self.open_mode)
        self.file_seek(prev_pos)

    def _file_send(self, msg):
        self._dedicated_send(msg)
        self.file_seek(self.file_size)

    @property
    def _file_size_recv(self):
        return self.file_size

    def _file_recv(self):
        if self.requires_refresh:
            self._file_refresh()
        if self.file_size > self._last_size:
            out = self._dedicated_recv()
            self.file_seek(self._file_size_recv)
        else:
            out = self.empty_bytes_msg
        return copy.deepcopy(out)
        
    @property
    def remaining_bytes(self):
        r"""int: Remaining bytes in the file."""
        if self.requires_refresh:
            self._file_refresh()
        return super(DedicatedFileBase, self).remaining_bytes

    # Methods that must be overriden by child classes
    def _dedicated_open(self, address, mode):  # pragma: debug
        raise NotImplementedError("Must be overriden by the base class.")

    def _dedicated_close(self):  # pragma: debug
        raise NotImplementedError("Must be overriden by the base class.")
    
    def _dedicated_send(self, msg):  # pragma: debug
        raise NotImplementedError("Must be overriden by the base class.")

    def _dedicated_recv(self):  # pragma: debug
        raise NotImplementedError("Must be overriden by the base class.")

    @classmethod
    def get_testing_options(cls, **kwargs):  # pragma: debug
        r"""Method to return a dictionary of testing options for this
        class.

        Returns:
            dict: Dictionary of variables to use for testing. Items:
                kwargs (dict): Keyword arguments for comms tested with
                    the provided content.
                send (list): List of objects to send to test file.
                recv (list): List of objects that will be received from a
                    test file that was sent the messages in 'send'.
                contents (bytes): Bytes contents of test file created by
                    sending the messages in 'send'.

        """
        raise NotImplementedError("Must be overriden by the base class.")
