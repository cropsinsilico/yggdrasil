# from logging import debug, error, exception
import os
from cis_interface.communication import CommBase


_N_FILES = 0


class FileComm(CommBase.CommBase):
    r"""Class for handling I/O from/to a file on disk.

    Args:
        name (str): The environment variable where communication address is
            stored.
        read_meth (str, optional): Method that should be used to read data
            from the file. Defaults to 'read'. Ignored if direction is 'send'.
        append (bool, optional): If True and writing, file is openned in append
            mode. Defaults to False.
        **kwargs: Additional keywords arguments are passed to parent class.

    Attributes:
        fd (file): File that should be read/written.
        read_meth (str): Method that should be used to read data from the file.
        append (bool): If True and writing, file is openned in append mode.

    Raises:
        ValueError: If the read_meth is not one of the supported values.

    """
    def __init__(self, name, read_meth='read', append=False, **kwargs):
        if not hasattr(self, 'fd'):
            self.fd = None
        if read_meth not in ['read', 'readline']:
            raise ValueError("read_meth '%s' not supported." % read_meth)
        self.read_meth = read_meth
        self.append = append
        super(FileComm, self).__init__(name, **kwargs)

    @property
    @staticmethod
    def comm_count(cls):
        r"""int: Number of communication connections."""
        return _N_FILES

    @classmethod
    def new_comm(cls, *args, **kwargs):
        r"""Initialize communication with new queue."""
        kwargs.setdefault('address', 'file.txt')
        return cls(*args, **kwargs)

    def open(self):
        r"""Open the file."""
        global _N_FILES
        if self.direction == 'recv':
            self.fd = open(self.address, 'rb')
        else:
            if self.append:
                self.fd = open(self.address, 'ab')
            else:
                self.fd = open(self.address, 'wb')
        _N_FILES += 1

    def close(self):
        r"""Close the file."""
        if self.is_open:
            self.fd.close()
        self.fd = None

    def remove_file(self):
        r"""Remove the file."""
        assert(self.is_closed)
        if os.path.isfile(self.address):
            os.remove(self.address)

    @property
    def is_open(self):
        r"""bool: True if the connection is open."""
        return (self.fd is not None)

    @property
    def remaining_bytes(self):
        r"""int: Remaining bytes in the file."""
        if self.is_closed or self.direction == 'send':
            return 0
        curpos = self.fd.tell()
        self.fd.seek(0, os.SEEK_END)
        endpos = self.fd.tell()
        self.fd.seek(curpos)
        return endpos - curpos

    @property
    def n_msg(self):
        r"""int: The number of messages in the file."""
        if self.is_closed or self.direction == 'send':
            return 0
        curpos = self.fd.tell()
        out = 0
        flag, msg = self._recv()
        while len(msg) != 0 and msg != self.eof_msg:
            out += 1
            flag, msg = self._recv()
        self.fd.seek(curpos)
        return out

    def on_send_eof(self):
        r"""Close file when EOF to be sent.

        Returns:
            bool: False so that message not sent.

        """
        self.close()
        return False

    def _send(self, msg):
        r"""Write message to a file.

        Args:
            msg (bytes, str): Data to write to the file.

        Returns:
            bool: Success or failure of writing to the file.

        """
        self.fd.write(msg)
        self.fd.flush()
        return True

    def _recv(self, timeout=0):
        r"""Reads message from a file.

        Returns:
            bool: Success or failure of reading from the file.

        """
        if self.read_meth == 'read':
            out = self.fd.read()
        elif self.read_meth == 'readline':
            out = self.fd.readline()
        if len(out) == 0:
            out = self.eof_msg
        return (True, out)
