import os
import copy
import tempfile
from yggdrasil import platform, tools, constants, serialize
from yggdrasil.communication import CommBase, AddressError
from yggdrasil.components import import_component


def is_file_like(x):
    r"""Check if an object is file-like via duck typing.

    Args:
        x (object): Object to check.

    Returns:
        bool: True if file-like, False otherwise.

    """
    return hasattr(x, 'read') and hasattr(x, 'write')


def convert_file(src, dst, src_type=None, dst_type=None,
                 src_kwargs=None, dst_kwargs=None, transform=None):
    r"""Convert from one file type to another.

    Args:
        src (str): Path to source file to convert.
        dst (str): Path to destination file that should be created.
        src_type (str, dict, optional): Name of source file type. If not
            provided, an attempt will be made to identify the file type
            from the extension.
        dst_type (str, dict, optional): Name of destination file type. If
            not provided, an attempt will be made to identify the file
            type from the extension.
        transform (dict, optional): Transform parameters for transforming
            messages between the soruce and destination file.

    Raises:
        IOError: If the source file does not exist.
        IOError: If the destination file exists.

    """
    if src_kwargs is None:
        src_kwargs = {}
    if dst_kwargs is None:
        dst_kwargs = {}
    # Check files
    if not os.path.isfile(src):
        raise IOError(f"Source file does not exist: {src}")
    if os.path.isfile(dst):
        raise IOError(f"Destination file already exists: {dst}")
    # Determine file types
    if src_type is None:
        src_type = constants.EXT2FILE[os.path.splitext(src)[1]]
    if dst_type is None:
        dst_type = constants.EXT2FILE[os.path.splitext(dst)[1]]
    # Load
    fsrc = import_component('file', src_type)(src, direction='recv',
                                              **src_kwargs)
    msg = fsrc.load(return_message_object=True)
    fsrc.close()
    # Transform
    if transform:
        dst_kwargs['transform'] = transform
    # Dump
    fdst = import_component('file', dst_type)(dst, direction='send',
                                              **dst_kwargs)
    fdst.update_serializer_from_message(msg)
    fdst.dump(msg)
    fdst.close()


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
        count (int, optional): When reading a file, read the file this
            many of times. Defaults to 0.
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
        'name': {'type': 'string',
                 'pattern': (r'^([A-Za-z0-9-_]+:)?\.?[A-Za-z0-9-_\\\/]+'
                             r'\.[A-Za-z0-9-_]+(::[A-Za-z0-9-_]+)?$')},
        'working_dir': {'type': 'string'},
        'filetype': {'type': 'string', 'default': _filetype,
                     'description': ('The type of file that will be read from '
                                     'or written to.')},
        'read_meth': {'type': 'string',
                      'enum': ['read', 'readline'],
                      'deprecated': True},
        'append': {'type': 'boolean', 'default': False},
        'in_temp': {'type': 'boolean', 'default': False},
        'is_series': {'type': 'boolean', 'default': False},
        'count': {'type': 'integer', 'default': 0},
        'wait_for_creation': {'type': 'number', 'default': 0.0},
        'serializer': {'allOf': [
            {'default': {}},
            {'$ref': '#/definitions/serializer'}]}}
    _schema_excluded_from_inherit = (
        ['commtype', 'datatype', 'read_meth', 'serializer']
        + CommBase.CommBase._model_schema_prop)
    _schema_base_class = None
    _schema_additional_kwargs = {'allowSingular': 'name'}
    _schema_additional_kwargs_no_inherit = {
        'pushProperties': {'$properties/serializer': True}}
    _default_serializer = 'direct'
    is_file = True
    _maxMsgSize = 0
    _mode_as_bytes = True
    _synchronous_read = False
    _deprecated_drivers = ['FileInputDriver', 'FileOutputDriver']

    def __init__(self, name, address=None, direction='send', **kwargs):
        self._external_fd = None
        if is_file_like(name):
            self._external_fd = name
            name = str(self._external_fd)
            if address is None:
                address = name
        elif is_file_like(address):
            self._external_fd = address
            address = str(self._external_fd)
        kwargs.setdefault('close_on_eof_send', True)
        kwargs['partner_language'] = None  # Files don't have partner comms
        return super(FileComm, self).__init__(
            name, address=address, direction=direction, **kwargs)

    @classmethod
    def _update_serializer_kwargs(cls, kwargs):
        r"""Update serializer information in a set of keyword arguments.

        Args:
            kwargs (dict): Keyword arguments containing non-schema behaved
                serializer information.

        """
        out = super(FileComm, cls)._update_serializer_kwargs(kwargs)
        if ((cls._default_serializer
             and cls._default_serializer != 'direct'
             and isinstance(out, dict)
             and out.get('seritype', 'direct') in ['default', 'direct'])):
            out['seritype'] = cls._default_serializer
        return out
        
    def _update_address(self, address):
        r"""Set the address based on the provided name.

        Args:
            address (str): Provided address.

        """
        try:
            super(FileComm, self)._update_address(address)
        except AddressError:
            if (((not self.wait_for_creation)
                 and self.direction == 'recv'
                 and not os.path.isfile(self.name_base))):
                raise AddressError(
                    f"File does not exist: '{self.name_base}'")
            self.address = self.name_base
        
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
        if self.append and os.path.isfile(self.current_address):
            self.disable_header()
        if getattr(self, 'read_meth', None) is None:
            self.read_meth = self.serializer.read_meth
        assert self.read_meth in ['read', 'readline']
        # Force overwrite for concatenation in append mode
        if self.append:
            if self.direction == 'recv':
                self.close_on_eof_recv = False
            elif (not self.concats_as_str):
                self.append = 'ow'
        # Assert that keyword args match serialization parameters
        if not self.concats_as_str:
            assert self.read_meth == 'read'
            assert not self.serializer.is_framed
        # Disable features not allowed when fd provided
        if self._external_fd:
            assert not self.is_series

    @property
    def concats_as_str(self):
        r"""bool: True if concatenating file contents result in a
        valid file."""
        return self.serializer.concats_as_str
            
    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class
        attributes prior to registration."""
        CommBase.CommBase.before_registration(cls)
        seri = None
        if cls._default_serializer:
            seri = import_component('serializer', cls._default_serializer)
            cls._extensions = seri.file_extensions
        # Add serializer properties to schema
        if cls._filetype != 'binary':
            assert 'serializer' not in cls._schema_properties
            if seri:
                new = seri._schema_properties
                cls._schema_properties.update(new)
            for k in ['driver', 'args', 'seritype']:
                cls._schema_properties.pop(k, None)
        cls._commtype = cls._filetype

    @classmethod
    def get_test_contents(cls, data, **kwargs):  # pragma: debug
        r"""Method for returning the serialized form of a set of test
        data.

        Args:
            data (list): List of test data objects to serialize.

        Returns:
            bytes: Serialized test data.

        """
        fname = f'contents_{cls._filetype}{cls._extensions[0]}'
        assert not os.path.isfile(fname)
        try:
            x = cls(fname, direction='send', append=True, **kwargs)
            for msg in data:
                x.send(msg)
            x.close()
            with open(fname, 'rb') as fd:
                out = fd.read()
        finally:
            if os.path.isfile(fname):
                os.remove(fname)
                cls.remove_companion_files(fname)
        return out

    @classmethod
    def get_testing_options(cls, read_meth=None, serializer=None, **kwargs):
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
        if serializer is None:
            serializer = cls._default_serializer
        out = super(FileComm, cls).get_testing_options(
            serializer=serializer, **kwargs)
        if 'read_meth' in cls._schema_properties:
            if read_meth is None:
                read_meth = 'read'
            out['kwargs']['read_meth'] = read_meth
        if read_meth == 'readline':
            out['recv_partial'] = [[x] for x in out['recv']]
            if serializer == 'direct':
                comment = tools.str2bytes(
                    cls._schema_properties['comment']['default']
                    + 'Comment\n')
                out['send'].append(comment)
                out['contents'] += comment
                out['recv_partial'].append([])
        else:
            seri_cls = import_component('serializer', serializer)
            if seri_cls.concats_as_str:
                out['recv_partial'] = [[x] for x in out['recv']]
                out['recv'] = seri_cls.concatenate(
                    out['recv'], **out['kwargs'])
            else:
                out['recv_partial'] = [[out['recv'][0]]]
                for i in range(1, len(out['recv'])):
                    out['recv_partial'].append(seri_cls.concatenate(
                        out['recv_partial'][-1] + [out['recv'][i]],
                        **out['kwargs']))
                out['recv'] = copy.deepcopy(out['recv_partial'][-1])
        return out
        
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
        
    @classmethod
    def underlying_comm_class(cls):
        r"""str: Name of underlying communication class."""
        return cls._filetype

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
        kwargs.setdefault('address', 'file%s' % cls._extensions[0])
        return args, kwargs

    @property
    def open_mode(self):
        r"""str: Mode that should be used to open the file."""
        if self.direction == 'recv':
            io_mode = 'r'
        elif self.append == 'ow':
            if self._synchronous_read:
                io_mode = 'a'
            else:
                io_mode = 'r+'
        elif self.append:
            io_mode = 'a'
        else:
            io_mode = 'w'
        if self._mode_as_bytes:
            io_mode += 'b'
        return io_mode

    def opp_comm_kwargs(self, for_yaml=False):
        r"""Get keyword arguments to initialize communication with opposite
        comm object.

        Args:
            for_yaml (bool, optional): If True, the returned dict will only
                contain values that can be specified in a YAML file. Defaults
                to False.

        Returns:
            dict: Keyword arguments for opposite comm object.

        """
        kwargs = super(FileComm, self).opp_comm_kwargs(for_yaml=for_yaml)
        kwargs.update(is_series=self.is_series,
                      count=self.count)
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
    @property
    def file_size(self):
        r"""int: Current size of file."""
        with self._closing_thread.lock:
            prev_pos = self.file_tell()
            self.file_seek(0, os.SEEK_END)
            out = self.file_tell() - prev_pos
            self.file_seek(0, 0)
            self.file_seek(prev_pos)
        return out

    def series_file_size(self, fname):
        r"""int: Size of file in series."""
        return os.path.getsize(fname)

    def file_tell(self):
        r"""int: Current position in the file."""
        with self._closing_thread.lock:
            return self.fd.tell()

    def file_seek(self, pos, whence=os.SEEK_SET):
        r"""Move in the file to the specified position.

        Args:
            pos (int): Position (in bytes) to move file to.
            whence (int, optional): Flag indicating position that pos
                is relative to. 0 for the beginning of the file, 1 for
                from the current location, and 2 from the end of the
                file.

        """
        with self._closing_thread.lock:
            self.fd.seek(pos, whence)

    def file_flush(self):
        r"""Flush the file."""
        with self._closing_thread.lock:
            self.fd.flush()

    def record_position(self):
        r"""Record the current position in the file/series."""
        _rec_pos = self.file_tell()
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
                self.file_seek(file_pos)
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
        if self.is_series or self.count:
            if series_index is None:
                series_index = self._series_index + 1
            if self._series_index != series_index:
                if (((self.direction == 'send') or self.count
                     or os.path.isfile(self.get_series_address(series_index)))):
                    with self._closing_thread.lock:
                        self._file_close()
                        self._series_index = series_index
                        self._open()
                    out = True
                    self.debug("Advanced to %d", series_index)
                if self.count:
                    self.count -= 1
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
    def _file_open(self, address, mode):
        return open(address, mode)
    
    def _open(self):
        address = self.current_address
        if self.fd is None:
            if (not os.path.isfile(address)) and (self.wait_for_creation > 0):
                T = self.start_timeout(self.wait_for_creation)
                while (not T.is_out) and (not os.path.isfile(address)):
                    self.sleep()
                self.stop_timeout()
            self._fd = self._file_open(address, self.open_mode)
        T = self.start_timeout()
        while (not T.is_out) and (not self.is_open):  # pragma: debug
            self.sleep()
        self.stop_timeout()
        if self.append == 'ow':
            try:
                self.file_seek(0, os.SEEK_END)
            except (AttributeError, ValueError):  # pragma: debug
                if self.is_open:
                    raise

    def _file_close(self):
        if self._external_fd:
            self._external_fd = None
        if self.is_open:
            try:
                self.file_flush()
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
        if not self._external_fd:
            self.register_comm(self.registry_key, self.fd)

    def _close(self, *args, **kwargs):
        r"""Close the file."""
        self._file_close()
        if ((self.is_series
             and os.path.isfile(self.current_address)
             and (os.path.getsize(self.current_address) == 0))):
            try:
                os.remove(self.current_address)
            except PermissionError:  # pragma: no cover
                pass
        if not self._external_fd:
            self.unregister_comm(self.registry_key)
        super(FileComm, self)._close(*args, **kwargs)

    def remove_file(self):
        r"""Remove the file."""
        assert self.is_closed
        if self.is_series:
            i = 0
            while True:
                address = self.get_series_address(i)
                if not os.path.isfile(address):
                    break
                os.remove(address)
                self.remove_companion_files(address)
                i += 1
        else:
            if os.path.isfile(self.address):
                os.remove(self.address)
                self.remove_companion_files(self.address)

    @classmethod
    def remove_companion_files(cls, address):
        r"""Remove companion files that are created when writing to a
        file

        Args:
            address (str): Address for the filename.

        """
        pass

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
        if self._external_fd:
            return self._external_fd
        return self._fd

    @property
    def remaining_bytes(self):
        r"""int: Remaining bytes in the file."""
        out = 0
        if self.is_closed or self.direction == 'send':
            return out
        with self._closing_thread.lock:
            pos = self.record_position()
            try:
                curpos = self.file_tell()
                self.file_seek(0, os.SEEK_END)
                endpos = self.file_tell()
                out = endpos - curpos
            except (ValueError, AttributeError, OSError):  # pragma: debug
                if self.is_open:
                    raise
            if self.is_series:
                i = self._series_index + 1
                while True:
                    fname = self.get_series_address(i)
                    if not os.path.isfile(fname):
                        break
                    out += self.series_file_size(fname)
                    i += 1
            self.change_position(*pos)
        return out

    @property
    def n_msg_recv(self):
        r"""int: The number of messages in the file."""
        with self._closing_thread.lock:
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

    def prepare_message(self, *args, **kwargs):
        r"""Perform actions preparing to send a message.

        Args:
            *args: Components of the outgoing message.
            **kwargs: Keyword arguments are passed to the parent class's method.

        Returns:
            CommMessage: Serialized and annotated message.

        """
        msg = super(FileComm, self).prepare_message(*args, **kwargs)
        if msg.flag == CommBase.FLAG_EOF:
            try:
                self.file_flush()
            except (AttributeError, ValueError):  # pragma: debug
                if self.is_open:
                    raise
            # self.close()
        return msg
        
    def serialize(self, obj, **kwargs):
        r"""Serialize a message using the associated serializer."""
        with self._closing_thread.lock:
            if (not self.concats_as_str) and self.is_open and (self.file_tell() != 0):
                new_obj = obj
                with open(self.current_address, 'rb') as fd:
                    old_obj = self.deserialize(fd.read())[0]
                obj = self.serializer.concatenate([old_obj, new_obj])
                assert len(obj) == 1
                obj = obj[0]
                # Reset file so that header will be written
                self.reset_position(truncate=True)
        return super(FileComm, self).serialize(obj, **kwargs)

    def _file_send(self, msg):
        self.fd.write(msg)
        if self.append == 'ow':
            self.fd.truncate()
            
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
                self._file_send(msg)
            self.file_flush()
        except (AttributeError, ValueError):  # pragma: debug
            if self.is_open:
                raise
            return False
        if (not self.is_eof(msg)) and self.is_series:
            self.advance_in_series()
            self.debug("Advanced to %d", self._series_index)
        return True

    def _file_recv(self):
        if self.read_meth == 'read':
            out = self.fd.read()
        elif self.read_meth == 'readline':
            out = self.fd.readline()
        else:  # pragma: debug
            raise NotImplementedError("Invalid read_meth: '%s'" % self.read_meth)
        return out

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
        prev_pos = 0
        try:
            self.read_header()
            prev_pos = self.file_tell()
            out = self._file_recv()
        except BaseException as e:  # pragma: debug
            # Use this to catch case where close called during receive.
            # In the future this should be handled via a lock.
            self.debug(f"Error during file receive: {type(e)}({e})")
            out = ''
        if len(out) == 0:
            if self.advance_in_series():
                self.debug("Advanced to %d", self._series_index)
                flag, out = self._recv()
            elif self.append and self.is_open:
                self.file_seek(prev_pos)
                out = self.empty_bytes_msg
            else:
                out = self.eof_msg
        else:
            if isinstance(out, bytes):
                out = out.replace(self.platform_newline, self.serializer.newline)
            if flag and (not self.is_eof(out)):
                if (((self.read_meth == 'readline')
                     and isinstance(out, bytes)
                     and out.startswith(self.serializer.comment))):
                    # Exclude comments
                    flag, out = self._recv()
                elif (((self.read_meth == 'read') and (prev_pos > 0)
                       and (not self.concats_as_str))):
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
                        self.file_seek(prev_pos + len1)
        return (flag, out)

    def purge(self):
        r"""Purge all messages from the comm."""
        if self.is_open and self.direction == 'recv':
            try:
                self.file_seek(0, os.SEEK_END)
            except (AttributeError, ValueError):  # pragma: debug
                if self.is_open:
                    raise

    def load(self, return_message_object=False, **kwargs):
        r"""Deserialize all contents from a file.

        Args:
            **kwargs: Keyword arguments are passed to recv calls.

        Returns:
            object: The deserialized data object or a list of
                deserialized data objects if there is more than one.

        Raises:
            SerializationError: If the first recv call fails.

        """
        from yggdrasil import rapidjson
        msg = self.recv(return_message_object=True, **kwargs)
        if not msg.flag:
            raise serialize.SerializationError(
                "Error deserializing from file")
        out = [msg]
        while msg.flag:
            msg = self.recv(return_message_object=True, **kwargs)
            if msg.flag:
                out.append(msg)
        if len(out) > 1:
            out[0].args = self.serializer.concatenate(
                [x.args for x in out])
            out[0].sinfo['datatype'] = rapidjson.encode_schema(
                out[0].args, minimal=True)
            out[0].stype = out[0].sinfo['datatype']
            for k in ['format_str', 'field_names', 'field_units']:
                if k in out[0].sinfo:
                    out[0].stype[k] = out[0].sinfo[k]
        out = out[0]
        if not return_message_object:
            out = out.args
        return out

    def dump(self, obj, **kwargs):
        r"""Serialize to a file.

        Args:
            **kwargs: Keyword arguments are passed to the send call.

        Raises:
            SerializationError: If the send call fails.

        """
        flag = self.send(obj, **kwargs)
        if not flag:
            raise serialize.SerializationError(
                "Error serializing to file")
