import os
from cis_interface.drivers.FileInputDriver import FileInputDriver
from cis_interface.dataio.AsciiFile import AsciiFile


class AsciiFileInputDriver(FileInputDriver):
    r"""Class that sends lines from an ASCII file.

    Args:
        name (str): Name of the queue that messages should be sent to.
        args (str or dict): Path to the file that messages should be read from
            or dictionary containing the filepath and other keyword arguments
            to be passed to the created AsciiFile object.
        skip_AsciiFile (bool, optional): If True, the AsciiFile instance is not
            created. Defaults to False.
        comment (str, optional): String that should be used to identify
                comments. Default set by :class:`AsciiFile`.
        newline (str, optional): String that should be used to identify
                the end of a line. Default set by :class:`AsciiFile`.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        file_kwargs (dict): Arguments used to create AsciiFile instance.
        file (:class:`AsciiFile.AsciiFile`): Associated special class for ASCII
            file.

    """
    def __init__(self, name, args, skip_AsciiFile=False, **kwargs):
        file_keys = ['comment', 'newline']
        file_kwargs = {}
        for k in file_keys:
            if k in kwargs:
                file_kwargs[k] = kwargs.pop(k)
        self.file_kwargs = file_kwargs
        super(AsciiFileInputDriver, self).__init__(name, args, **kwargs)
        self.debug('(%s)', args)
        if skip_AsciiFile:
            self.file = None
        else:
            self.file = AsciiFile(self.args, 'r', **self.file_kwargs)
        self.debug('(%s): done with init', args)

    def close_file(self):
        r"""Close the file."""
        self.debug(':close_file()')
        with self.lock:
            self.file.close()
        
    def run(self):
        r"""Run the driver. The file is opened and then data is read from the
        file and sent to the message queue until eof is encountered or the file
        is closed.
        """
        self.debug(':run in %s', os.getcwd())
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
                self.ipc_send(self.eof_msg)
                break
            if data is not None:
                self.debug(':run: read: %d bytes', len(data))
                self.ipc_send(data)
                nread += 1
        if nread == 0:  # pragma: debug
            self.debug(':run, no input')
        self.debug(':run returned')
