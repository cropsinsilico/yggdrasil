import os
from cis_interface.drivers.FileDriver import FileDriver


class FileInputDriver(FileDriver):
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
        super(FileInputDriver, self).__init__(name, args, suffix="_IN",
                                              **kwargs)
        self.debug('(%s)', args)

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
            ret = self.ipc_send(data)
            self.debug(":run send failed")
        self.debug(':run returned')
