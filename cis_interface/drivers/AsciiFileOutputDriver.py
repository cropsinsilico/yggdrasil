from cis_interface.drivers.FileOutputDriver import FileOutputDriver
from cis_interface.dataio.AsciiFile import AsciiFile


class AsciiFileOutputDriver(FileOutputDriver):
    r"""Class to handle output line by line to an ASCII file.

    Args:
        name (str): Name of the output queue to receive messages from.
        args (str or dict): Path to the file that messages should be written to
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
        super(AsciiFileOutputDriver, self).__init__(name, args, **kwargs)
        self.debug('(%s)', args)
        # self.file_kwargs['format_str'] = ''
        if skip_AsciiFile:
            self.file = None
        else:
            self.file = AsciiFile(self.args, 'w', **self.file_kwargs)
        self.debug('(%s): done with init', self.args)

    @property
    def is_open(self):
        r"""bool: True if file is open, False otherwise."""
        with self.lock:
            return self.file.is_open

    def open_file(self):
        r"""Open the file."""
        self.debug(':open_file()')
        with self.lock:
            self.file.open()

    def close_file(self):
        r"""Close the file."""
        self.debug(':close_file()')
        with self.lock:
            self.file.close()

    def file_write(self, data):
        r"""When a message is received, write it as a full line to the file.

        Args:
            data (str): Message.

        """
        with self.lock:
            self.file.writeline_full(data)
