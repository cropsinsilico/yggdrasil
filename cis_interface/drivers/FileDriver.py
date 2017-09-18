import os
from cis_interface.drivers.IODriver import IODriver


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

    def close_file(self):
        r"""Close the file."""
        self.debug(':close_file()')
        with self.lock:
            if self.fd:
                self.fd.close()
            self.fd = None

    def terminate(self):
        r"""Terminate the driver, closeing the file as necessary."""
        self.debug(':terminate()')
        self.close_file()
        print 'closed_file'
        super(FileDriver, self).terminate()
