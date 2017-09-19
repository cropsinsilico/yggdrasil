import os
from cis_interface.drivers.IODriver import IODriver
from cis_interface.interface.PsiInterface import PSI_MSG_EOF


class FileDriver(IODriver):
    r"""Class to handle I/O of messages from/to a file.

    Args:
        name (str): Name of the ipc queue to receive messages from.
        args (str): Path to the file that messages should be written to or read
            from.
        suffix (str, optional): Suffix for ipc queue. "_IN" for input, "_OUT"
            for output.
        \*\*kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    Attributes (in addition to parent class's):
        args (str): Path to the file that messages should be written to.
        fd (file-like): File descriptor for the target file if open.
        lock (:class:`threading.Lock`): Lock to be used when accessing file.

    """
    def __init__(self, name, args, suffix=None, **kwargs):
        super(FileDriver, self).__init__(name, suffix, **kwargs)
        self.debug('(%s)', args)
        self.args = os.path.abspath(args)
        self.fd = None

    @property
    def eof_msg(self):
        r"""str: Message indicating end of file."""
        return PSI_MSG_EOF

    @property
    def is_open(self):
        r"""bool: True if file is open, false otherwise."""
        with self.lock:
            out = (self.fd is not None)
        return out

    @property
    def is_valid(self):
        r"""bool: True if the file is open and parent is valid."""
        out = super(FileDriver, self).is_valid
        return (out and (self.is_open))

    def close_file(self):
        r"""Close the file."""
        self.debug(':close_file()')
        with self.lock:
            if self.is_open:
                self.fd.close()
            self.fd = None

    def terminate(self):
        r"""Terminate the driver, closeing the file as necessary."""
        if self._terminated:
            self.debug(':terminated() Driver already terminated.')
            return
        self.debug(':terminate()')
        self.close_file()
        super(FileDriver, self).terminate()

    def graceful_stop(self):
        r"""Gracefully stop the driver by closing the queues then waiting for
        files to close."""
        self.debug(':graceful_stop()')
        super(FileDriver, self).graceful_stop()
        self.close_queue()
        T = self.start_timeout()
        while (self.is_open and not T.is_out):
            self.sleep()
        self.stop_timeout()
