import os
from cis_interface.drivers.AsciiFileInputDriver import AsciiFileInputDriver
from cis_interface.dataio.AsciiTable import AsciiTable
from cis_interface.tools import eval_kwarg


class AsciiTableInputDriver(AsciiFileInputDriver):
    r"""Class to handle input from an ASCII table.

    Args:
        name (str): Name of the input queue to send messages to.
        args (str or dict): Path to the file that messages should be read from
            or dictionary containing the filepath and other keyword arguments
            to be passed to the created AsciiTable object.
        format_str (str): Format string that should be used to format
            output in the case that the io_mode is 'w' (write). It is not
            required if the io_mode is any other value.
        dtype (str): Numpy structured data type for each row. If not
            provided it is set using format_str. Defaults to None.
        column_names (list, optional): List of column names. Defaults to
            None.
        use_astropy (bool, optional): If True, astropy is used to determine
            a table's format if it is installed. If False, a format string
            must be contained in the table. Defaults to False.
        column (str, optional): String that should be used to separate
            columns. Default set by :class:`AsciiTable`.
        comment (str, optional): String that should be used to identify
            comments. Default set by :class:`AsciiFile`.
        newline (str, optional): String that should be used to identify
            the end of a line. Default set by :class:`AsciiFile`.
        as_array (bool, optional): If True, the table contents are sent all at
            once as an array. Defaults to False.
        \*\*kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    Attributes (in additon to parent class's):
        file (:class:`AsciiTable.AsciiTable`): Associated special class for
            ASCII table.
        as_array (bool): If True, the table contents are sent all at once as an
            array.

    """
    def __init__(self, name, args, as_array=False, **kwargs):
        file_keys = ['format_str', 'dtype', 'column_names', 'use_astropy',
                     'column']
        file_kwargs = {}
        for k in file_keys:
            if k in kwargs:
                file_kwargs[k] = kwargs.pop(k)
                if k in ['column_names', 'use_astropy']:
                    file_kwargs[k] = eval_kwarg(file_kwargs[k])
        super(AsciiTableInputDriver, self).__init__(
            name, args, skip_AsciiFile=True, **kwargs)
        self.debug('(%s)', args)
        self.file_kwargs.update(**file_kwargs)
        self.as_array = eval_kwarg(as_array)
        self.file = AsciiTable(self.args, 'r', **self.file_kwargs)
        self.debug('(%s): done with init', args)

    def run(self):
        r"""Run the driver. The file is opened and then data is read from the
        file and sent to the message queue until eof is encountered or the file
        is closed.
        """
        self.debug(':run in %s', os.getcwd())
        self.ipc_send(self.file.format_str)
        if self.as_array:
            with self.lock:
                data = self.file.read_bytes(order='F')
            self.debug(':run: read: %d bytes', len(data))
            self.ipc_send_nolimit(data)
        else:
            with self.lock:
                self.file.open()
            nread = 0
            while self.file.is_open:
                with self.lock:
                    if self.file.is_open:
                        eof, data = self.file.readline_full()
                    else:  # pragma: debug
                        break
                if eof:
                    self.debug(':run, End of file encountered')
                    self.ipc_send_nolimit(self.eof_msg)
                    break
                elif (data is not None):
                    self.debug(':run: read: %d bytes', len(data))
                    self.ipc_send_nolimit(data)
                    nread += 1
            if nread == 0:  # pragma: debug
                self.debug(':run, no input')
        self.debug(':run returned')
