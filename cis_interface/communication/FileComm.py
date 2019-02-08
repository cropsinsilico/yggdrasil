import os
import tempfile
from cis_interface import backwards, platform
from cis_interface.communication import CommBase
from cis_interface.schema import register_component, inherit_schema
from cis_interface.serialize.DirectSerialize import DirectSerialize


@register_component
class FileComm(CommBase.CommBase):
    r"""Class for handling I/O from/to a file on disk.

    >>> x = FileComm('test_send', address='test_file.txt', direction='send')
    >>> x.send('Test message')
    True
    >>> with open('test_file.txt', 'r') as fd:
    ...     print(fd.read())
    Test message
    >>> x = FileComm('test_recv', address='test_file.txt', direction='recv')
    >>> x.recv()
    (True, b'Test message')

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
        is_series (bool, optional): If True, input/output will be done to
            a series of files. If reading, each file will be processed until
            the end is reached. If writing, each output will be to a new
            file in the series. The addressed is assumed to contain a format
            for the index of the file. Defaults to False.
        wait_for_creation (float, optional): Time (in seconds) that should be
            waited before opening for the file to be created if it dosn't exist.
            Defaults to 0 s and file will attempt to be opened immediately.
        **kwargs: Additional keywords arguments are passed to parent class.

    Attributes:
        fd (file): File that should be read/written.
        read_meth (str): Method that should be used to read data from the file.
        append (bool): If True and writing, file is openned in append mode.
        in_temp (bool): If True, the path will be considered relative to the
            platform temporary directory.
        open_as_binary (bool): If True, the file is opened in binary mode.
        newline (str): String indicating a new line.
        is_series (bool): If True, input/output will be done to a series of
            files. If reading, each file will be processed until the end is
            reached. If writing, each output will be to a new file in the series.
        platform_newline (str): String indicating a newline on the current
            platform.

    Raises:
        ValueError: If the read_meth is not one of the supported values.

    """

    _filetype = 'binary'
    _datatype = {'type': 'bytes'}
    _schema_type = 'file'
    _schema_required = ['name', 'filetype', 'working_dir']
    _schema_properties = inherit_schema(
        CommBase.CommBase._schema_properties,
        {'working_dir': {'type': 'string'},
         'filetype': {'type': 'string', 'default': _filetype},
         'append': {'type': 'boolean', 'default': False},
         'in_temp': {'type': 'boolean', 'default': False},
         'is_series': {'type': 'boolean', 'default': False},
         'wait_for_creation': {'type': 'float', 'default': 0.0}},
        remove_keys=['commtype', 'datatype'], **DirectSerialize._schema_properties)
    _default_serializer = DirectSerialize
    _attr_conv = ['newline', 'platform_newline']
    _default_extension = '.txt'
    is_file = True
    _maxMsgSize = 0

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('close_on_eof_send', True)
        return super(FileComm, self).__init__(*args, **kwargs)

    def _init_before_open(self, read_meth='read', open_as_binary=True, **kwargs):
        r"""Get absolute path and set attributes."""
        super(FileComm, self)._init_before_open(**kwargs)
        # Process file class keywords
        if not hasattr(self, '_fd'):
            self._fd = None
        if read_meth not in ['read', 'readline']:
            raise ValueError("read_meth '%s' not supported." % read_meth)
        self.read_meth = read_meth
        self.platform_newline = platform._newline
        if self.in_temp:
            self.address = os.path.join(tempfile.gettempdir(), self.address)
        self.address = os.path.abspath(self.address)
        self.open_as_binary = open_as_binary
        self._series_index = 0
        # Put string attributes in the correct format
        if self.open_as_binary:
            func_conv = backwards.as_bytes
        else:
            func_conv = backwards.as_unicode
        for k in self._attr_conv:
            v = getattr(self, k)
            if v is not None:
                setattr(self, k, func_conv(v))

    @classmethod
    def get_testing_options(cls, read_meth='read', open_as_binary=True, **kwargs):
        r"""Method to return a dictionary of testing options for this class.

        Returns:
            dict: Dictionary of variables to use for testing. Key/value pairs:
                kwargs (dict): Keyword arguments for comms tested with the
                    provided content.
                send (list): List of objects to send to test file.
                recv (list): List of objects that will be received from a test
                    file that was sent the messages in 'send'.
                contents (bytes): Bytes contents of test file created by sending
                    the messages in 'send'.

        """
        out = super(FileComm, cls).get_testing_options(**kwargs)
        out['kwargs']['read_meth'] = read_meth
        out['kwargs']['open_as_binary'] = open_as_binary
        if (read_meth == 'read') and isinstance(out['recv'][0], backwards.bytes_type):
            out['recv'] = [b''.join(out['recv'])]
        if not open_as_binary:
            out['contents'] = out['contents'].replace(
                backwards.match_stype(out['contents'], '\n'),
                backwards.match_stype(out['contents'], platform._newline))
        return out
        
    @classmethod
    def is_installed(cls, language=None):
        r"""Determine if the necessary libraries are installed for this
        communication class.

        Args:
            language (str, optional): Specific language that should be checked
                for compatibility. Defaults to None and all languages supported
                on the current platform will be checked.

        Returns:
            bool: Is the comm installed.

        """
        # Filesystem is implied
        return True

    @classmethod
    def underlying_comm_class(self):
        r"""str: Name of underlying communication class."""
        return 'FileComm'

    @classmethod
    def close_registry_entry(cls, value):
        r"""Close a registry entry."""
        out = False
        if not value.closed:  # pragma: debug
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
        elif self.append == 'ow':
            io_mode = 'r+'
        elif self.append:
            io_mode = 'a'
        else:
            io_mode = 'w'
        if self.open_as_binary:
            io_mode += 'b'
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
        kwargs['is_series'] = self.is_series
        return kwargs

    @property
    def registry_key(self):
        r"""str: String used to register the socket."""
        # return self.address
        return '%s_%s_%s' % (self.address, self.direction, self.uuid)

    def record_position(self):
        r"""Record the current position in the file/series."""
        _rec_pos = self.fd.tell()
        _rec_ind = self._series_index
        return _rec_pos, _rec_ind

    def change_position(self, file_pos, series_index=None):
        r"""Change the position in the file/series.

        Args:
            file_pos (int): Position that should be moved to in the file.
            series_index (int, optinal): Index of the file in the series that
                should be moved to. Defaults to None and will be set to the
                current series index.

        """
        if series_index is None:
            series_index = self._series_index
        self.advance_in_series(series_index)
        self.advance_in_file(file_pos)

    def advance_in_file(self, file_pos):
        r"""Advance to a certain position in the current file.

        Args:
            file_pos (int): Position that should be moved to in the current.
                file.

        """
        if self.is_open:
            try:
                self.fd.seek(file_pos)
            except (AttributeError, ValueError):  # pragma: debug
                if self.is_open:
                    raise

    def advance_in_series(self, series_index=None):
        r"""Advance to a certain file in a series.

        Args:
            series_index (int, optional): Index of file in the series that
                should be moved to. Defaults to None and call will advance to
                the next file in the series.

        Returns:
            bool: True if the file was advanced in the series, False otherwise.

        """
        out = False
        if self.is_series:
            if series_index is None:
                series_index = self._series_index + 1
            if self._series_index != series_index:
                if (((self.direction == 'send')
                     or os.path.isfile(self.get_series_address(series_index)))):
                    self._file_close()
                    self._series_index = series_index
                    self._open()
                    out = True
                    self.debug("Advanced to %d", series_index)
        return out

    def get_series_address(self, index=None):
        r"""Get the address of a file in the series.

        Args:
            index (int, optional): Index in series to get address for.
                Defaults to None and the current index is used.

        Returns:
            str: Address for the file in the series.

        """
        if index is None:
            index = self._series_index
        return self.address % index

    @property
    def current_address(self):
        r"""str: Address of file currently being used."""
        if self.is_series:
            address = self.get_series_address()
        else:
            address = self.address
        return address
        
    def _open(self):
        address = self.current_address
        if self.fd is None:
            if (not os.path.isfile(address)) and (self.wait_for_creation > 0):
                T = self.start_timeout(self.wait_for_creation)
                while (not T.is_out) and (not os.path.isfile(address)):
                    self.sleep()
                self.stop_timeout()
            self._fd = open(address, self.open_mode)
        T = self.start_timeout()
        while (not T.is_out) and (not self.is_open):  # pragma: debug
            self.sleep()
        self.stop_timeout()
        if self.append == 'ow':
            try:
                self.fd.seek(0, os.SEEK_END)
            except (AttributeError, ValueError):  # pragma: debug
                if self.is_open:
                    raise

    def _file_close(self):
        if self.is_open:
            try:
                self.fd.flush()
                os.fsync(self.fd.fileno())
            except OSError:  # pragma: debug
                pass
            try:
                self.fd.close()
            except (AttributeError, ValueError):  # pragma: debug
                if self.is_open:
                    raise
        self._fd = None

    def open(self):
        r"""Open the file."""
        super(FileComm, self).open()
        self._open()
        self.register_comm(self.registry_key, self.fd)

    def _close(self, *args, **kwargs):
        r"""Close the file."""
        self._file_close()
        self.unregister_comm(self.registry_key)
        super(FileComm, self)._close(*args, **kwargs)

    def remove_file(self):
        r"""Remove the file."""
        assert(self.is_closed)
        if self.is_series:
            i = 0
            while True:
                address = self.get_series_address(i)
                if not os.path.isfile(address):
                    break
                os.remove(address)
                i += 1
        else:
            if os.path.isfile(self.address):
                os.remove(self.address)

    @property
    def is_open(self):
        r"""bool: True if the connection is open."""
        try:
            return (self.fd is not None) and (not self.fd.closed)
        except AttributeError:  # pragma: debug
            if self.fd is not None:
                raise
            return False

    @property
    def fd(self):
        r"""Associated file identifier."""
        return self._fd

    @property
    def remaining_bytes(self):
        r"""int: Remaining bytes in the file."""
        if self.is_closed or self.direction == 'send':
            return 0
        pos = self.record_position()
        try:
            curpos = self.fd.tell()
            self.fd.seek(0, os.SEEK_END)
            endpos = self.fd.tell()
            out = endpos - curpos
        except (ValueError, AttributeError):  # pragma: debug
            if self.is_open:
                raise
            out = 0
        if self.is_series:
            i = self._series_index + 1
            while True:
                fname = self.get_series_address(i)
                if not os.path.isfile(fname):
                    break
                out += os.path.getsize(fname)
                i += 1
        self.change_position(*pos)
        return out

    @property
    def n_msg_recv(self):
        r"""int: The number of messages in the file."""
        if self.is_closed:
            return 0
        if self.read_meth == 'read':
            return int(self.remaining_bytes > 0)
        elif self.read_meth == 'readline':
            pos = self.record_position()
            try:
                out = 0
                flag, msg = self._recv()
                while len(msg) != 0 and msg != self.eof_msg:
                    out += 1
                    flag, msg = self._recv()
            except ValueError:  # pragma: debug
                out = 0
            self.change_position(*pos)
        else:  # pragma: debug
            self.error('Unsupported read_meth: %s', self.read_meth)
            out = 0
        return out

    def on_send_eof(self):
        r"""Close file when EOF to be sent.

        Returns:
            bool: False so that message not sent.

        """
        flag, msg_s = super(FileComm, self).on_send_eof()
        try:
            self.fd.flush()
        except (AttributeError, ValueError):  # pragma: debug
            if self.is_open:
                raise
        # self.close()
        return flag, msg_s

    def _send(self, msg):
        r"""Write message to a file.

        Args:
            msg (bytes, str): Data to write to the file.

        Returns:
            bool: Success or failure of writing to the file.

        """
        try:
            if msg != self.eof_msg:
                if not self.open_as_binary:
                    msg = backwards.as_unicode(msg)
                self.fd.write(msg)
                if self.append == 'ow':
                    self.fd.truncate()
            self.fd.flush()
        except (AttributeError, ValueError):  # pragma: debug
            if self.is_open:
                raise
            return False
        if msg != self.eof_msg and self.is_series:
            self.advance_in_series()
            self.debug("Advanced to %d", self._series_index)
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
        flag = True
        try:
            if self.read_meth == 'read':
                out = self.fd.read()
            elif self.read_meth == 'readline':
                out = self.fd.readline()
        except BaseException:  # pragma: debug
            # Use this to catch case where close called during receive.
            # In the future this should be handled via a lock.
            out = ''
        if len(out) == 0:
            if self.advance_in_series():
                self.debug("Advanced to %d", self._series_index)
                flag, out = self._recv()
            else:
                out = self.eof_msg
        else:
            out = out.replace(self.platform_newline, self.newline)
        if not self.open_as_binary:
            out = backwards.as_bytes(out)
        return (flag, out)

    def purge(self):
        r"""Purge all messages from the comm."""
        if self.is_open and self.direction == 'recv':
            try:
                self.fd.seek(0, os.SEEK_END)
            except (AttributeError, ValueError):  # pragma: debug
                if self.is_open:
                    raise
