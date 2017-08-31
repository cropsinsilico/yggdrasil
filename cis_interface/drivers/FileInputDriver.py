from threading import Lock
from logging import *
import os
import time
from IODriver import IODriver

class FileInputDriver(IODriver):
    r"""Class that sends messages read from a file.

    Args:
        name (str): Name of the queue that messages should be sent to.
        args (str): Path to the file that messages should be read from.
        \*\*kwargs: Additional keyword arguments are passed to parent class's
            __init__ method. 

    Attributes (in additon to parent class's):
        args (str): Path to the file that messages should be read from.
        fd (file-like): File descriptor for the input file while it is open.
        lock (:class:`threading.Lock`): Lock to be used when accessing file.

    """
    def __init__(self, name, args, **kwargs):
        super(FileInputDriver, self).__init__(name, "_IN", **kwargs)
        self.debug('(%s)', args)
        self.args = os.path.abspath(args)
        self.fd = None
        self.debug('(%s): done with init', args)

    def close_file(self):
        r"""Close the file."""
        self.debug(':close_file()')
        with self.lock:
            if self.fd:
                self.fd.close()
            self.fd = None

    def terminate(self):
        r"""Terminate the driver. The file is closed as necessary."""
        self.debug(':terminate()')
        super(FileInputDriver, self).terminate()
        self.close_file()

    def run(self):
        r"""Run the driver. The file is opened and then data is read from the
        file and sent to the message queue until eof is encountered or the file
        is closed.
        """
        self.debug(':run in %s', os.getcwd())
        try:
            with self.lock:
                self.fd = open(self.args, 'rb')
        except:  # pragma: debug
            self.exception('Could not open file.')
            return
        with self.lock:
            if self.fd is None:  # pragma: debug
                data = ''
            else:
                data = self.fd.read()
        self.debug(':run: read: %d bytes', len(data))
        if len(data) == 0:  # pragma: debug
            self.debug(':run, no input')
        else:
            self.ipc_send(data)
        self.debug(':run returned')

