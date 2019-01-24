import numpy as np
from cis_interface import serialize, backwards, units
from cis_interface.communication.AsciiFileComm import AsciiFileComm
from cis_interface.schema import register_component, inherit_schema
from cis_interface.serialize.AsciiTableSerialize import AsciiTableSerialize


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
    _schema_properties = inherit_schema(
        AsciiFileComm._schema_properties,
        {'as_array': {'type': 'boolean', 'default': False},
         'field_names': {'type': 'array', 'items': {'type': 'string'}},
         'field_units': {'type': 'array', 'items': {'type': 'string'}}},
        **AsciiTableSerialize._schema_properties)
    _default_serializer = AsciiTableSerialize
    _attr_conv = AsciiFileComm._attr_conv + ['delimiter', 'format_str']

    def _init_before_open(self, **kwargs):
        r"""Set up dataio and attributes."""
        self.header_was_read = False
        self.header_was_written = False
        super(AsciiTableComm, self)._init_before_open(**kwargs)
        if self.serializer.as_array:
            self.read_meth = 'read'
        else:
            self.read_meth = 'readline'
        if self.append:
            self.header_was_written = True
        
    @classmethod
    def get_testing_options(cls, as_array=False, **kwargs):
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
        out = super(AsciiFileComm, cls).get_testing_options(as_array=as_array,
                                                            **kwargs)
        field_names = [backwards.as_str(x) for
                       x in out['kwargs']['field_names']]
        field_units = [backwards.as_str(x) for
                       x in out['kwargs']['field_units']]
        if as_array:
            lst = out['send'][0]
            out['recv'] = [[units.add_units(np.hstack([x[i] for x in out['send']]), u)
                            for i, (n, u) in enumerate(zip(field_names, field_units))]]
            out['dict'] = {k: l for k, l in zip(field_names, lst)}
            out['msg_array'] = serialize.list2numpy(lst, names=field_names)
        else:
            out['recv'] = out['send']
            out['dict'] = {k: v for k, v in zip(field_names, out['send'][0])}
        out['field_names'] = field_names
        out['field_units'] = field_units
        return out
    
    def read_header(self):
        r"""Read header lines from the file and update serializer info."""
        if self.header_was_read:
            return
        pos = self.record_position()
        self.change_position(0)
        serialize.discover_header(self.fd, self.serializer,
                                  newline=self.newline,
                                  comment=self.comment,
                                  delimiter=self.delimiter)
        self.change_position(*pos)
        self.header_was_read = True

    def write_header(self):
        r"""Write header lines to the file based on the serializer info."""
        if self.header_was_written:
            return
        header_msg = serialize.format_header(
            format_str=self.serializer.format_str,
            field_names=self.serializer.get_field_names(as_bytes=True),
            field_units=self.serializer.get_field_units(as_bytes=True),
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
