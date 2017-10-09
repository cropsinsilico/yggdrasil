# from logging import debug, error, exception
from cis_interface.communication.AsciiFileComm import AsciiFileComm
from cis_interface.dataio.AsciiTable import AsciiTable


class AsciiTableComm(AsciiFileComm):
    r"""Class for handling I/O from/to a file on disk.

    Args:
        name (str): The environment variable where communication address is
            stored.
        as_array (bool, optional): If True, table IO is done for entire array.
            Otherwise, the table is read/written line by line. Defaults to False.
        **kwargs: Additional keywords arguments are passed to parent class.

    Attributes:
        file_kwargs (dict): Keyword arguments for the AsciiTable instance.
        file (AsciiTable): Instance for read/writing to/from file.
        as_array (bool): If True, table IO is done for entire array. Otherwise,
            the table is read/written line by line.
        array_was_read (bool): If True, the table array was already read in.

    """
    def __init__(self, name, as_array=False, dont_open=False, **kwargs):
        file_keys = ['format_str', 'dtype', 'column_names', 'column'
                     'use_astropy']
        file_kwargs = {}
        for k in file_keys:
            if k in kwargs:
                file_kwargs[k] = kwargs.pop(k)
        self.array_was_read = False
        super(AsciiTableComm, self).__init__(name, dont_open=True,
                                             skip_AsciiFile=True, **kwargs)
        self.file_kwargs.update(**file_kwargs)
        self.as_array = as_array
        if self.direction == 'recv':
            self.file = AsciiTable(self.address, 'r', **self.file_kwargs)
        else:
            if self.append:
                self.file = AsciiTable(self.address, 'a', **self.file_kwargs)
            else:
                self.file = AsciiTable(self.address, 'w', **self.file_kwargs)
        if not dont_open:
            self.open()

    def opp_comm_kwargs(self):
        r"""Get keyword arguments to initialize communication with opposite
        comm object.

        Returns:
            dict: Keyword arguments for opposite comm object.

        """
        kwargs = super(AsciiTableComm, self).opp_comm_kwargs()
        kwargs['format_str'] = self.file.format_str
        kwargs['dtype'] = self.file.dtype
        kwargs['column_names'] = self.file.column_names
        kwargs['column'] = self.file.column
        kwargs['use_astropy'] = self.file.use_astropy
        kwargs['as_array'] = self.as_array
        return kwargs

    @property
    def n_msg(self):
        r"""int: The number of messages in the file."""
        if ((self.is_open and self.direction == 'recv' and self.as_array and
             not self.array_was_read)):
            if self.remaining_bytes > 0:
                out = 1
            else:
                out = 0
        else:
            out = super(AsciiTableComm, self).n_msg
        return out

    def _send(self, msg):
        r"""Write message to a file.

        Args:
            msg (bytes, str): Data to write to the file.

        Returns:
            bool: Success or failure of writing to the file.

        """
        if self.as_array:
            self.file.write_bytes(msg, order='F', append=True)
        else:
            self.file.writeline_full(msg, validate=True)
        self.file.fd.flush()
        return True

    def _recv(self, timeout=0, **kwargs):
        r"""Reads message from a file.

        Returns:
            tuple(bool, str): Success or failure of reading from the file.

        """
        if self.as_array:
            if self.array_was_read:
                flag = True
                data = self.eof_msg
            else:
                if self.remaining_bytes > 0:
                    flag = True
                    data = self.file.read_bytes(order='F')
                    self.array_was_read = True
                else:
                    flag = True
                    data = self.eof_msg
            # Only read the table array once
            # self.close()
        else:
            flag, data = super(AsciiTableComm, self)._recv(dont_parse=True)
        return (flag, data)
