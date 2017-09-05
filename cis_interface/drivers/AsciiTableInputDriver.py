import os
from cis_interface.drivers.AsciiFileInputDriver import AsciiFileInputDriver
from cis_interface.dataio.AsciiTable import AsciiTable


class AsciiTableInputDriver(AsciiFileInputDriver):
    r"""Class to handle input from an ASCII table.

    Args:
        name (str): Name of the input queue to send messages to.
        args (str or dict): Path to the file that messages should be read from
            or dictionary containing the filepath and other keyword arguments
            to be passed to the created AsciiTable object.
        \*\*kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    Attributes (in additon to parent class's):
        file (:class:`AsciiTable.AsciiTable`): Associated special class for
            ASCII table.
        as_array (bool): If True, the table contents are sent all at once as an
            array. Defaults to False if not set in args dict.

    """
    def __init__(self, name, args, **kwargs):
        super(AsciiTableInputDriver, self).__init__(
            name, args, skip_AsciiFile=True, **kwargs)
        self.debug('(%s)', args)
        self.as_array = self.file_kwargs.pop('as_array', False)
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
