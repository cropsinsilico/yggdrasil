import os
from cis_interface.drivers.FileDriver import FileDriver


class FileOutputDriver(FileDriver):
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
        super(FileOutputDriver, self).__init__(name, args, suffix="_OUT",
                                               **kwargs)
        self.debug('(%s)', args)

    def open_file(self):
        r"""Open the file."""
        self.debug(':open_file()')
        with self.lock:
            self.fd = open(self.args, 'wb+')

    def file_recv(self):
        r"""Receive a message from the output queue.

        Returns:
            str: Received message.

        """
        self.debug(':file_recv()')
        with self.lock:
            return self.ipc_recv()

    def file_write(self, data):
        r"""When a message is received, write it to the file.

        Args:
            data (str): Received message.

        """
        with self.lock:
            self.fd.write(data)

    def run(self):
        r"""Run the driver. The driver will open the file and write receieved
        messages to the file as they are received until the file is closed.
        """
        self.debug(':run in %s', os.getcwd())
        try:
            self.open_file()
        except:  # pragma: debug
            self.exception('Could not open file.')
            return
        while self.is_valid:
            # Ensure queue not closed between check and message
            with self.lock:
                if self.queue_open:
                    data = self.file_recv()
                else:  # pragma: debug
                    self.debug(':run: Queue closed')
                    break
            if data is None:  # pragma: debug
                # Break on None for closed queue
                self.debug(':run: Queue closed')
                break
            elif data == self.eof_msg:
                # Break on end of file
                self.debug(':run: End of file')
                break
            elif len(data) > 0:
                self.debug(':run: Received %s bytes', len(data))
                # Ensure file not closed between check and write
                with self.lock:
                    if self.is_open:
                        self.file_write(data)
                    else:  # pragma: debug
                        # Break on file closed
                        self.debug(':run: File closed')
                        break
            else:
                # Sleep if there is not any data
                self.debug(':run: No data, checkin again in  %f s',
                           self.sleeptime)
                self.sleep()
        self.close_file()
        self.debug(':run returns')
