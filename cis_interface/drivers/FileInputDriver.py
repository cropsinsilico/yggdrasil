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

    def open_file(self):
        r"""Open the file."""
        self.debug(':open_file()')
        with self.lock:
            self.fd = open(self.args, 'rb')

    def file_read(self):
        r"""Read a message from the file.

        Returns:
            str: Message.

        """
        with self.lock:
            data = self.fd.read()
            if len(data) == 0:
                data = self.eof_msg
        return data

    def file_send(self, data):
        r"""Send a message to the IPC queue.

        Args:
            data (str): Message.

        Returns:
            bool: Success or failure of send.

        """
        with self.lock:
            return self.ipc_send(data)

    def on_eof(self):
        r"""Actions to perform when the end of file is reached."""
        pass

    def run(self):
        r"""Run the driver. The file is opened and then data is read from the
        file and sent to the message queue until eof is encountered or the file
        is closed.
        """
        self.debug(':run in %s', os.getcwd())
        try:
            self.open_file()
        except:  # pragma: debug
            self.exception('Could not open file.')
            return
        nread = 0
        nsent = 0
        while self.is_valid:
            # Ensure file not closed between check and read
            with self.lock:
                if self.is_open:
                    data = self.file_read()
                else:  # pragma: debug
                    # Break on file closed
                    self.debug(':run: File closed.')
                    break
            if data is None:  # pragma: debug
                # Break on None for closed file
                self.debug(':run: File closed.')
                break
            elif data == self.eof_msg:
                # Break on end of file
                self.debug(':run: End of file')
                self.on_eof()
                break
            else:
                nread += 1
                self.debug(':run: Read %d bytes.', len(data))
                # Ensure queue not closed between check and message
                with self.lock:
                    if self.queue_open:
                        ret = self.file_send(data)
                        if ret:
                            nsent += 1
                    else:  # pragma: debug
                        # Break on queue closed
                        self.debug(':run: Queue closed')
                        break
        self.close_file()
        self.debug(':run: Read %d messages, sent %d.' % (nread, nsent))
        self.debug(':run returns')
