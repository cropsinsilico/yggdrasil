from cis_interface.communication import FileComm
from cis_interface.schema import register_component
from cis_interface.serialize.MatSerialize import MatSerialize


@register_component
class MatFileComm(FileComm.FileComm):
    r"""Class for handling I/O from/to a Matlab .mat file on disk.

    Args:
        name (str): The environment variable where file path is stored.
        **kwargs: Additional keywords arguments are passed to parent class.

    """

    _filetype = 'mat'
    _default_serializer = MatSerialize
    _default_extension = '.mat'

    def __init__(self, name, **kwargs):
        kwargs.setdefault('readmeth', 'read')
        if kwargs.get('append', False):
            kwargs['append'] = 'ow'
        super(MatFileComm, self).__init__(name, **kwargs)

    @classmethod
    def get_testing_options(cls):
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
        out = super(MatFileComm, cls).get_testing_options()
        out['exact_contents'] = False  # Contains a time stamp
        # Appending the same message only results in the same message because
        # it is updated as a dictionary
        out['recv'] = [out['msg']]
        return out

    def _send(self, msg):
        r"""Write message to a file.

        Args:
            msg (bytes, str): Data to write to the file.

        Returns:
            bool: Success or failure of writing to the file.

        """
        if self.append and (msg != self.eof_msg):
            self.fd.seek(0, 0)
            prev = self.deserialize(self.fd.read())[0]
            prev.update(self.deserialize(msg)[0])
            msg = self.serialize(prev)
            self.fd.seek(0, 0)
        return super(MatFileComm, self)._send(msg)
