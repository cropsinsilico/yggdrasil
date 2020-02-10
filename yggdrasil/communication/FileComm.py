import os
import copy
import tempfile
from yggdrasil import platform, tools
from yggdrasil.serialize.SerializeBase import SerializeBase
from yggdrasil.communication import CommBase


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
            mode. If True and reading, file is kept open even if the end of the
            file is reached to allow for another process to write to the file in
            append mode. Defaults to False.
        in_temp (bool, optional): If True, the path will be considered relative
            to the platform temporary directory. Defaults to False.
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
    _schema_subtype_key = 'filetype'
    _schema_subtype_description = ('The entire file is read/written all at '
                                   'once as bytes.')
    _schema_required = ['name', 'filetype', 'working_dir', 'serializer']
    _schema_properties = {
        'working_dir': {'type': 'string'},
        'filetype': {'type': 'string', 'default': _filetype,
                     'description': ('The type of file that will be read from '
                                     'or written to.')},
        'read_meth': {'type': 'string', 'default': 'read',
                      'enum': ['read', 'readline']},
        'append': {'type': 'boolean', 'default': False},
        'in_temp': {'type': 'boolean', 'default': False},
        'is_series': {'type': 'boolean', 'default': False},
        'wait_for_creation': {'type': 'float', 'default': 0.0},
        'serializer': {'oneOf': [{'$ref': '#/definitions/serializer'},
                                 {'type': 'instance',
                                  'class': SerializeBase}],
                       'default': {'seritype': 'direct'}}}
    _schema_excluded_from_inherit = (
        ['commtype', 'datatype', 'read_meth', 'serializer']
        + CommBase.CommBase._model_schema_prop)
    _schema_excluded_from_class_validation = ['serializer']
    _schema_base_class = None
    _default_serializer = 'direct'
    _default_extension = '.txt'
    is_file = True
    _maxMsgSize = 0

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('close_on_eof_send', True)
        kwargs['partner_language'] = None  # Files don't have partner comms
        return super(FileComm, self).__init__(*args, **kwargs)

    def _init_before_open(self, **kwargs):
        r"""Get absolute path and set attributes."""
        self.header_was_read = False
        self.header_was_written = False
        super(FileComm, self)._init_before_open(**kwargs)
        # Process file class keywords
        if not hasattr(self, '_fd'):
            self._fd = None
        self.platform_newline = platform._newline
        if self.in_temp:
            self.address = os.path.join(tempfile.gettempdir(), self.address)
        self.address = os.path.abspath(self.address)
        self._series_index = 0
        if self.append:
            self.disable_header()
        if 'read_meth' not in self._schema_properties:
            self.read_meth = self.serializer.read_meth
        assert(self.read_meth in ['read', 'readline'])
        # Force overwrite for concatenation in append mode
        if self.append:
            if self.direction == 'recv':
                self.close_on_eof_recv = False
            elif (not self.serializer.concats_as_str):
                self.append = 'ow'
        # Assert that keyword args match serialization parameters
        if not self.serializer.concats_as_str:
            assert(self.read_meth == 'read')
            assert(not self.serializer.is_framed)
            
    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration."""
        CommBase.CommBase.before_registration(cls)
        # Add serializer properties to schema
        if cls._filetype != 'binary':
            assert('serializer' not in cls._schema_properties)
            cls._schema_properties.update(
                cls._default_serializer_class._schema_properties)
            del cls._schema_properties['seritype']

    @classmethod
    def get_testing_options(cls, read_meth=None, **kwargs):
        r"""Method to return a dictionary of testing options for this class.

        Args:
            read_meth (str, optional): Read method that will be used by the test
                class. Defaults to None and will be set by the serialier.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method and the serializers methods for determining the
                default read_meth and concatenating the sent objects into the
                objects that are expected to be received.

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
        if 'read_meth' in cls._schema_properties:
            if read_meth is None:
                read_meth = cls._schema_properties['read_meth']['default']
            out['kwargs']['read_meth'] = read_meth
        if read_meth == 'readline':
            out['recv_partial'] = [[x] for x in out['recv']]
            if cls._default_serializer == 'direct':
                comment = tools.str2bytes(
                    cls._schema_properties['comment']['default']
                    + 'Comment\n')
                out['send'].append(comment)
                out['contents'] += comment
                out['recv_partial'].append([])
        else:
            seri_cls = cls._default_serializer_class
            if seri_cls.concats_as_str:
                out['recv_partial'] = [[x] for x in out['recv']]
                out['recv'] = seri_cls.concatenate(out['recv'], **out['kwargs'])
            else:
                out['recv_partial'] = [[out['recv'][0]]]
                for i in range(1, len(out['recv'])):
                    out['recv_partial'].append(seri_cls.concatenate(
                        out['recv_partial'][-1] + [out['recv'][i]], **out['kwargs']))
                out['recv'] = copy.deepcopy(out['recv_partial'][-1])
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
        io_mode += 'b'
        return io_mode

    def opp_comm_kwargs(self):
        r"""Get keyword arguments to initialize communication with opposite
        comm object.

        Returns:
            dict: Keyword arguments for opposite comm object.

        """
        kwargs = super(FileComm, self).opp_comm_kwargs()
        kwargs['is_series'] = self.is_series
        return kwargs

    @property
    def registry_key(self):
        r"""str: String used to register the socket."""
        # return self.address
        return '%s_%s_%s' % (self.address, self.direction, self.uuid)

    # Methods related to header
    def enable_header(self):
        r"""Turn on header so that it will be written."""
        self.header_was_read = False
        self.header_was_written = False
        if self.serializer.has_header:
            self.serializer.enable_file_header()
    
    def disable_header(self):
        r"""Turn off header so that it will not be written."""
        self.header_was_read = True
        self.header_was_written = True
        if self.serializer.has_header:
            self.serializer.disable_file_header()
    
    def read_header(self):
        r"""Read header lines from the file and update serializer info."""
        if self.header_was_read:
            return
        if self.serializer.has_header:
            pos = self.record_position()
            self.serializer.deserialize_file_header(self.fd)
            self.change_position(*pos)
        self.header_was_read = True

    def write_header(self):
        r"""Write header lines to the file based on the serializer info."""
        if self.header_was_written:
            return
        if self.serializer.has_header:
            header_msg = self.serializer.serialize_file_header()
            if header_msg:
                self.fd.write(header_msg)
        self.header_was_written = True

    # Methods related to position in the file/series
    def record_position(self):
        r"""Record the current position in the file/series."""
        _rec_pos = self.fd.tell()
        _rec_ind = self._series_index
        return _rec_pos, _rec_ind, self.header_was_read, self.header_was_written

    def reset_position(self, truncate=False):
        r"""Move to the front of the file and allow header to be read again.

        Args:
            truncate (bool, optional): If True, the file will be truncated after
                moving to the beginning, effectively erasing the file. Defaults
                to False.

        """
        self.change_position(0)
        self.enable_header()
        if truncate:
            self.fd.truncate()

    def change_position(self, file_pos, series_index=None,
                        header_was_read=None, header_was_written=None):
        r"""Change the position in the file/series.

        Args:
            file_pos (int): Position that should be moved to in the file.
            series_index (int, optinal): Index of the file in the series that
                should be moved to. Defaults to None and will be set to the
                current series index.
            header_was_read (bool, optional): Status of if header has been
                read or not. Defaults to None and will be set to the current
                value.
            header_was_written (bool, optional): Status of if header has been
                written or not. Defaults to None and will be set to the current
                value.

        """
        if series_index is None:
            series_index = self._series_index
        if header_was_read is None:
            header_was_read = self.header_was_read
        if header_was_written is None:
            header_was_written = self.header_was_written
        self.advance_in_series(series_index)
        self.advance_in_file(file_pos)
        self.header_was_read = header_was_read
        self.header_was_written = header_was_written

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
        if out:
            self.header_was_read = False
            self.header_was_written = False
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

    # Methods related to opening/closing the file
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
        except (ValueError, AttributeError, OSError):  # pragma: debug
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
                while len(msg) != 0 and (not self.is_eof(msg)):
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

    def serialize(self, obj, **kwargs):
        r"""Serialize a message using the associated serializer."""
        if (not self.serializer.concats_as_str) and (self.fd.tell() != 0):
            new_obj = obj
            with open(self.current_address, 'rb') as fd:
                old_obj = self.deserialize(fd.read())[0]
            obj = self.serializer.concatenate([old_obj, new_obj])
            assert(len(obj) == 1)
            obj = obj[0]
            # Reset file so that header will be written
            self.reset_position(truncate=True)
        return super(FileComm, self).serialize(obj, **kwargs)
            
    def _send(self, msg):
        r"""Write message to a file.

        Args:
            msg (bytes, str): Data to write to the file.

        Returns:
            bool: Success or failure of writing to the file.

        """
        # Write header
        if not self.is_eof(msg):
            self.write_header()
        # Write message
        try:
            if not self.is_eof(msg):
                self.fd.write(msg)
                if self.append == 'ow':
                    self.fd.truncate()
            self.fd.flush()
        except (AttributeError, ValueError):  # pragma: debug
            if self.is_open:
                raise
            return False
        if (not self.is_eof(msg)) and self.is_series:
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
            self.read_header()
            prev_pos = self.fd.tell()
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
            elif self.append and self.is_open:
                self.fd.seek(prev_pos)
                out = self.empty_bytes_msg
            else:
                out = self.eof_msg
        else:
            out = out.replace(self.platform_newline, self.serializer.newline)
            if flag and (not self.is_eof(out)):
                if (((self.read_meth == 'readline')
                     and out.startswith(self.serializer.comment))):
                    # Exclude comments
                    flag, out = self._recv()
                elif (((self.read_meth == 'read') and (prev_pos > 0)
                       and (not self.serializer.concats_as_str))):
                    # Rewind file and read entire contents if data was added to
                    # the file type using a serialization method that dosn't
                    # concatenate
                    self.reset_position()
                    flag, out = self._recv()
                elif (self.read_meth == 'read') and self.serializer.is_framed:
                    # Rewind if more than one frame read
                    len0 = len(out)
                    out = self.serializer.get_first_frame(out)
                    len1 = len(out)
                    if (len1 > 0) and (len0 != len1):
                        self.fd.seek(prev_pos + len1)
        return (flag, out)

    def purge(self):
        r"""Purge all messages from the comm."""
        if self.is_open and self.direction == 'recv':
            try:
                self.fd.seek(0, os.SEEK_END)
            except (AttributeError, ValueError):  # pragma: debug
                if self.is_open:
                    raise
