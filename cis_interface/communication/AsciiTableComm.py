from cis_interface import serialize, backwards
from cis_interface.communication.AsciiFileComm import AsciiFileComm


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
        self.fd.seek(0)
        serialize.discover_header(self.fd, self.serializer,
                                  newline=self.newline, comment=self.comment,
                                  delimiter=self.delimiter)
        self.delimiter = self.serializer.table_info['delimiter']
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
