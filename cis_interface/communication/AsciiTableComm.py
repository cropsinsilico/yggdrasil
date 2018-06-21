from cis_interface import serialize, backwards
from cis_interface.communication.AsciiFileComm import AsciiFileComm
from cis_interface.schema import register_component, inherit_schema


@register_component
class AsciiTableComm(AsciiFileComm):
    r"""Class for handling I/O from/to a file on disk.

    Args:
        name (str): The environment variable where communication address is
            stored.
        delimiter (str, optional): String that should be used to separate
            columns. If not provided and format_str is not set prior to I/O,
            this defaults to whitespace.
        use_astropy (bool, optional): If True and the astropy package is
            installed, it will be used to read/write the table. Defaults to
            False.
        **kwargs: Additional keywords arguments are passed to parent class.

    """
    
    _filetype = 'table'
    _schema = inherit_schema(AsciiFileComm._schema, 'filetype', _filetype,
                             delimiter={'type': 'string', 'required': False},
                             use_astropy={'type': 'boolean', 'required': False})

    def _init_before_open(self, delimiter=None, use_astropy=False,
                          serializer_kwargs=None, **kwargs):
        r"""Set up dataio and attributes."""
        if serializer_kwargs is None:
            serializer_kwargs = {}
        self.header_was_read = False
        self.header_was_written = False
        serializer_kwargs.update(stype=3, use_astropy=use_astropy)
        kwargs['serializer_kwargs'] = serializer_kwargs
        super(AsciiTableComm, self)._init_before_open(**kwargs)
        if self.serializer.as_array:
            self.read_meth = 'read'
        else:
            self.read_meth = 'readline'
        if self.append:
            self.header_was_written = True
        if delimiter is None:
            delimiter = serialize._default_delimiter
        self.delimiter = backwards.unicode2bytes(delimiter)
        
    def read_header(self):
        r"""Read header lines from the file and update serializer info."""
        if self.header_was_read:
            return
        pos = self.record_position()
        self.change_position(0)
        serialize.discover_header(self.fd, self.serializer,
                                  newline=self.newline, comment=self.comment,
                                  delimiter=self.delimiter)
        self.delimiter = self.serializer.table_info['delimiter']
        self.change_position(*pos)
        self.header_was_read = True

    def write_header(self):
        r"""Write header lines to the file based on the serializer info."""
        if self.header_was_written:
            return
        header_msg = serialize.format_header(
            format_str=self.serializer.format_str,
            field_names=self.serializer.field_names,
            field_units=self.serializer.field_units,
            comment=self.comment, newline=self.newline,
            delimiter=self.delimiter)
        self.fd.write(header_msg)
        self.header_was_written = True

    def record_position(self):
        r"""Record the current position in the file/series."""
        pos, ind = super(AsciiTableComm, self).record_position()
        return pos, ind, self.header_was_read, self.header_was_written

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
        if header_was_read is None:
            header_was_read = self.header_was_read
        if header_was_written is None:
            header_was_written = self.header_was_written
        super(AsciiTableComm, self).change_position(file_pos, series_index)
        self.header_was_read = header_was_read
        self.header_was_written = header_was_written

    def advance_in_series(self, *args, **kwargs):
        r"""Advance to a certain file in a series.

        Args:
            index (int, optional): Index of file in the series that should be
                moved to. Defaults to None and call will advance to the next
                file in the series.

        Returns:
            bool: True if the file was advanced in the series, False otherwise.

        """
        out = super(AsciiTableComm, self).advance_in_series(*args, **kwargs)
        if out:
            self.header_was_read = False
            self.header_was_written = False
        return out

    def _send(self, msg):
        r"""Write message to a file.

        Args:
            msg (bytes, str): Data to write to the file.

        Returns:
            bool: Success or failure of writing to the file.

        """
        if msg != self.eof_msg:
            self.write_header()
        return super(AsciiTableComm, self)._send(msg)

    def _recv(self, timeout=0, **kwargs):
        r"""Reads message from a file.

        Args:
            timeout (float, optional): Time in seconds to wait for a message.
                Defaults to self.recv_timeout. Unused.

        Returns:
            tuple(bool, str): Success or failure of reading from the file.

        """
        self.read_header()
        return super(AsciiTableComm, self)._recv(timeout=timeout, **kwargs)
