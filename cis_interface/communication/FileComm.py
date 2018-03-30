import os
import tempfile
from cis_interface import backwards, platform
from cis_interface.communication import CommBase


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
        in_temp (bool, optional): If True, the path will be considered relative
            to the platform temporary directory. Defaults to False.

    Raises:
        ValueError: If the read_meth is not one of the supported values.

    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('close_on_eof_send', True)
        return super(FileComm, self).__init__(*args, **kwargs)

    def _init_before_open(self, read_meth='read', append=False, in_temp=False,
                          **kwargs):
        r"""Get absolute path and set attributes."""
        super(FileComm, self)._init_before_open(**kwargs)
        if not hasattr(self, '_fd'):
            self._fd = None
        if read_meth not in ['read', 'readline']:
            raise ValueError("read_meth '%s' not supported." % read_meth)
        self.read_meth = read_meth
        self.append = append
        if in_temp:
            self.address = os.path.join(tempfile.gettempdir(), self.address)
        self.address = os.path.abspath(self.address)
        self.is_file = True

    @property
    def maxMsgSize(self):
        r"""int: Maximum size of a single message that should be sent."""
        return 0

    @classmethod
    def underlying_comm_class(self):
        r"""str: Name of underlying communication class."""
        return 'FileComm'

    @classmethod
    def close_registry_entry(cls, value):
        r"""Close a registry entry."""
        out = False
        if not value.closed:
            value.close()
            out = True
        return out

    @classmethod
    def new_comm_kwargs(cls, *args, **kwargs):
        r"""Initialize communication with new queue."""
        kwargs.setdefault('address', 'file.txt')
        return args, kwargs

    def _open(self):
        if self.direction == 'recv':
            self._fd = open(self.address, 'rb')
        else:
            if self.append:
                self._fd = open(self.address, 'ab')
            else:
                self._fd = open(self.address, 'wb')

    def _file_close(self):
        if self.is_open:
            try:
                self.fd.flush()
                os.fsync(self.fd.fileno())
            except OSError:  # pragma: debug
                pass
            self.fd.close()
        self._fd = None

    def open(self):
        r"""Open the file."""
        super(FileComm, self).open()
        self._open()
        self.register_comm(self.address, self.fd)

    def _close(self, *args, **kwargs):
        r"""Close the file."""
        self._file_close()
        self.unregister_comm(self.address)
        super(FileComm, self)._close(*args, **kwargs)

    def remove_file(self):
        r"""Remove the file."""
        assert(self.is_closed)
        if os.path.isfile(self.address):
            os.remove(self.address)

    @property
    def is_open(self):
        r"""bool: True if the connection is open."""
        return (self.fd is not None) and (not self.fd.closed)

    @property
    def fd(self):
        r"""Associated file identifier."""
        return self._fd

    @property
    def remaining_bytes(self):
        r"""int: Remaining bytes in the file."""
        if self.is_closed or self.direction == 'send':
            return 0
        try:
            curpos = self.fd.tell()
            self.fd.seek(0, os.SEEK_END)
            endpos = self.fd.tell()
            self.fd.seek(curpos)
        except ValueError:  # pragma: debug
            return 0
        return endpos - curpos

    @property
    def n_msg_recv(self):
        r"""int: The number of messages in the file."""
        if self.is_closed:
            return 0
        if self.read_meth == 'read':
            return int(self.remaining_bytes > 0)
        elif self.read_meth == 'readline':
            try:
                curpos = self.fd.tell()
                out = 0
                flag, msg = self._recv()
                while len(msg) != 0 and msg != self.eof_msg:
                    out += 1
                    flag, msg = self._recv()
                self.fd.seek(curpos)
            except ValueError:  # pragma: debug
                out = 0
        else:  # pragma: debug
            self.error('Unsupported read_meth: %s', self.read_meth)
            out = 0
        return out

    def on_send_eof(self):
        r"""Close file when EOF to be sent.

        Returns:
            bool: False so that message not sent.

        """
        flag = super(FileComm, self).on_send_eof()
        self.fd.flush()
        # self.close()
        return flag

    def _send(self, msg):
        r"""Write message to a file.

        Args:
            msg (bytes, str): Data to write to the file.

        Returns:
            bool: Success or failure of writing to the file.

        """
        if msg != self.eof_msg:
            self.fd.write(msg)
        self.fd.flush()
        return True

    def _recv(self, timeout=0):
        r"""Reads message from a file.

        Args:
            timeout (float, optional): Time in seconds to wait for a message.
                Defaults to self.recv_timeout. Unused.

        Returns:
            bool: Success or failure of reading from the file.

        """
        if self.read_meth == 'read':
            out = self.fd.read()
        elif self.read_meth == 'readline':
            out = self.fd.readline()
        else:  # pragma: debug
            self.error('Unsupported read_meth: %s', self.read_meth)
            out = ''
        if len(out) == 0:
            out = self.eof_msg
        else:
            out = out.replace(backwards.unicode2bytes(platform._newline),
                              backwards.unicode2bytes('\n'))
        return (True, out)

    def purge(self):
        r"""Purge all messages from the comm."""
        if self.is_open and self.direction == 'recv':
            self.fd.seek(0, os.SEEK_END)
