import os
import tempfile
from cis_interface import backwards, platform, serialize
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
        in_temp (bool, optional): If True, the path will be considered relative
            to the platform temporary directory. Defaults to False.
        open_as_binary (bool, optional): If True, the file is opened in binary
            mode. Defaults to True.
        newline (str, optional): String indicating a new line. Defaults to
            serialize._default_newline.
        **kwargs: Additional keywords arguments are passed to parent class.

    Attributes:
        fd (file): File that should be read/written.
        read_meth (str): Method that should be used to read data from the file.
        append (bool): If True and writing, file is openned in append mode.
        in_temp (bool): If True, the path will be considered relative to the
            platform temporary directory.
        open_as_binary (bool): If True, the file is opened in binary mode.
        newline (str): String indicating a new line.
        platform_newline (str): String indicating a newline on the current
            platform.

    Raises:
        ValueError: If the read_meth is not one of the supported values.

    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('close_on_eof_send', True)
        return super(FileComm, self).__init__(*args, **kwargs)

    def _init_before_open(self, read_meth='read', append=False, in_temp=False,
                          open_as_binary=True, newline=None, **kwargs):
        r"""Get absolute path and set attributes."""
        super(FileComm, self)._init_before_open(**kwargs)
        if not hasattr(self, '_fd'):
            self._fd = None
        if read_meth not in ['read', 'readline']:
            raise ValueError("read_meth '%s' not supported." % read_meth)
        self.read_meth = read_meth
        self.append = append
        if newline is None:
            newline = serialize._default_newline
        self.newline = newline
        self.platform_newline = platform._newline
        self.in_temp = in_temp
        if self.in_temp:
            self.address = os.path.join(tempfile.gettempdir(), self.address)
        self.address = os.path.abspath(self.address)
        self.open_as_binary = open_as_binary
        self.is_file = True
        # Put string attributes in the correct format
        attr_conv = ['newline', 'platform_newline']
        if self.open_as_binary:
            func_conv = backwards.unicode2bytes
        else:
            func_conv = backwards.bytes2unicode
        for k in attr_conv:
            v = getattr(self, k)
            if v is not None:
                setattr(self, k, func_conv(v))

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

    @property
    def open_mode(self):
        r"""str: Mode that should be used to open the file."""
        if self.direction == 'recv':
            io_mode = 'r'
        elif self.append:
            io_mode = 'a'
        else:
            io_mode = 'w'
        if self.open_as_binary:
            return io_mode + 'b'
        else:
            return io_mode

    def opp_comm_kwargs(self):
        r"""Get keyword arguments to initialize communication with opposite
        comm object.

        Returns:
            dict: Keyword arguments for opposite comm object.

        """
        kwargs = super(FileComm, self).opp_comm_kwargs()
        kwargs['newline'] = self.newline
        kwargs['open_as_binary'] = self.open_as_binary
        return kwargs

    def _open(self):
        self._fd = open(self.address, self.open_mode)

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
            if not self.open_as_binary:
                msg = backwards.bytes2unicode(msg)
            self.fd.write(msg)
        self.fd.flush()
        return True

    def _recv(self, timeout=0):
        r"""Reads message from a file.

        Args:
            timeout (float, optional): Time in seconds to wait for a message.
                Defaults to self.recv_timeout. Unused.

        Returns:
            tuple (bool, str): Success or failure of reading from the file and
                the read messages as bytes.

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
            out = out.replace(self.platform_newline, self.newline)
        if not self.open_as_binary:
            out = backwards.unicode2bytes(out)
        return (True, out)

    def purge(self):
        r"""Purge all messages from the comm."""
        if self.is_open and self.direction == 'recv':
            self.fd.seek(0, os.SEEK_END)
