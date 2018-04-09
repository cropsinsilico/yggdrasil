from cis_interface import serialize, backwards
from cis_interface.communication.AsciiFileComm import AsciiFileComm


class AsciiTableComm(AsciiFileComm):
    r"""Class for handling I/O from/to a file on disk.

    Args:
        name (str): The environment variable where communication address is
            stored.
        format_str (str, optional): C style format string specifying how rows
            in the table should be formated. Defaults to None. If receiving
            from a file, this will be determined from the file contents during
            the first read. If sending to a file, this must be updated before
            anything can be written.
        delimiter (str, optional): String that should be used to separate
            columns. If not provided and format_str is not set prior to I/O,
            this defaults to whitespace.
        column_names (list, optional): Names that should be written to the
            table header. Defaults to None.
        column_units (list, optional): Units that should be written to the
            table header. Defaults to None.
        use_astropy (bool, optional): If True and the astropy package is
            installed, it will be used to read/write the table. Defaults to
            False.
        as_array (bool, optional): If True, table IO is done for entire array.
            Otherwise, the table is read/written line by line. Defaults to False.
        **kwargs: Additional keywords arguments are passed to parent class.

    Attributes:
        as_array (bool): If True, table IO is done for entire array. Otherwise,
            the table is read/written line by line.

    """
    def _init_before_open(self, format_str=None, delimiter=None,
                          column_names=None, column_units=None,
                          as_array=False, use_astropy=False,
                          serializer_kwargs=None, **kwargs):
        r"""Set up dataio and attributes."""
        if serializer_kwargs is None:
            serializer_kwargs = {}
        self.header_was_read = False
        self.header_was_written = False
        serializer_kwargs.update(stype=3, format_str=format_str,
                                 field_names=column_names,
                                 field_units=column_units,
                                 as_array=as_array, use_astropy=use_astropy)
        kwargs['serializer_kwargs'] = serializer_kwargs
        super(AsciiTableComm, self)._init_before_open(**kwargs)
        self.as_array = self.serializer.as_array
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
        header_lines = []
        header_size = 0
        self.fd.seek(0)
        for line in self.fd:
            sline = backwards.unicode2bytes(
                line.replace(self.platform_newline, self.newline))
            if not sline.startswith(self.comment):
                break
            header_size += len(line)
            header_lines.append(sline)
        # Parse header & set serializer attributes
        header = serialize.parse_header(header_lines)
        for k in ['format_str', 'field_names', 'field_units']:
            if header.get(k, False):
                setattr(self.serializer, k, header[k])
        # Try to determine format from array without header
        if self.serializer.format_str is None:
            all_contents = self.fd.read()
            arr = serialize.table_to_array(all_contents,
                                           names=self.serializer.field_names,
                                           comment=self.comment,
                                           delimiter=self.delimiter)
            self.serializer.field_names = arr.dtype.names
            self.serializer.format_str = serialize.table2format(
                arr.dtype, delimiter=self.delimiter, comment=self.comment,
                newline=self.newline)
        self.delimiter = self.serializer.table_info['delimiter']
        # Seek to just after the header
        self.fd.seek(header_size)
        self.header_was_read = True

    def write_header(self):
        r"""Write header lines to the file based on the serializer info."""
        if self.header_was_written:
            return
        header_msg = serialize.format_header(
            format_str=self.serializer.format_str,
            field_names=self.serializer.field_names,
            field_units=self.serializer.field_units,
            comment=self.comment, newline=self.newline)
        self.fd.write(header_msg)
        self.header_was_written = True

    def _send(self, msg):
        r"""Write message to a file.

        Args:
            msg (bytes, str): Data to write to the file.

        Returns:
            bool: Success or failure of writing to the file.

        """
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
