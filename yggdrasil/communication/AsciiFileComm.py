from yggdrasil.communication.FileComm import FileComm


class AsciiFileComm(FileComm):
    r"""Class for handling I/O from/to a file on disk.

    Args:
        name (str): The environment variable where communication address is
            stored.
        comment (str, optional): String indicating a comment. If 'read_meth'
            is 'readline' and this is provided, lines starting with a comment
            will be skipped.
        **kwargs: Additional keywords arguments are passed to parent class.

    """

    _filetype = 'ascii'
    _schema_subtype_description = ('This file is read/written as encoded text '
                                   'one line at a time.')

    def _init_before_open(self, **kwargs):
        r"""Get absolute path and set attributes."""
        super(AsciiFileComm, self)._init_before_open(**kwargs)
        self.read_meth = 'readline'

    @classmethod
    def get_testing_options(cls, **kwargs):
        r"""Method to return a dictionary of testing options for this class.

        Returns:
            dict: Dictionary of variables to use for testing. Key/value pairs:
                kwargs (dict): Keyword arguments for comms tested with the
                    provided content.
                send (list): List of objects to send to test file.
                recv (list): List of objects that will be received from a test
                    file that was sent the messages in 'send'.
                contents (bytes): Bytes contents of test file created by sending
                    the messages in 'send'.

        """
        kwargs['read_meth'] = 'readline'
        return super(AsciiFileComm, cls).get_testing_options(**kwargs)
