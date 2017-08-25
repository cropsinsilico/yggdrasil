from threading import Lock
from logging import *
import time
import os
from IODriver import IODriver

class FileOutputDriver(IODriver):
    r"""Class to handle output of received messages to a file.

    Args:
        name (str): Name of the output queue to receive messages from.
        args (str): Path to the file that messages should be written to.
        \*\*kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    Attributes (in addition to parent class's):
        args (str): Path to the file that messages should be written to.
        fd (file-like): File descriptor for the target file if open.
        lock (:class:`threading.Lock`): Lock to be used when accessing file. 

    """
    def __init__(self, name, args, **kwargs):
        super(FileOutputDriver, self).__init__(name, "_OUT", **kwargs)
        self.debug('(%s)', args)
        self.args = os.path.abspath(args)
        self.fd = None
        self.lock = Lock()
        self.debug('(%s): done with init', args)

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
        super(FileOutputDriver, self).terminate()
        self.close_file()

    def run(self):
        r"""Run the driver. The driver will open the file and write receieved
        messages to the file as they are received until the file is closed.
        """
        self.debug(':run in %s', os.getcwd())
        try:
            with self.lock:
                self.fd = open(self.args, 'w+')
        except:
            self.exception('Could not open file.')
            return
        while self.fd is not None:
            data = self.ipc_recv()
            if data is None:
                self.debug(':recv: closed')
                break
            self.debug(':recvd %s bytes', len(data))
            if len(data) > 0:
                with self.lock:
                    if self.fd is None:
                        break
                    else:
                        self.fd.write(data)
            else:
                self.debug(':recv: no data')
                self.sleep()
        self.debug(':run returns')


