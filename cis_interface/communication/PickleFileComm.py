from cis_interface import backwards
from cis_interface.communication import FileComm
from cis_interface.schema import register_component
from cis_interface.serialize.PickleSerialize import PickleSerialize


@register_component
class PickleFileComm(FileComm.FileComm):
    r"""Class for handling I/O from/to a pickled file on disk.

    Args:
        name (str): The environment variable where file path is stored.
        **kwargs: Additional keywords arguments are passed to parent class.

    """

    _filetype = 'pickle'
    _default_serializer = PickleSerialize

    def __init__(self, name, **kwargs):
        kwargs.setdefault('readmeth', 'read')
        super(PickleFileComm, self).__init__(name, **kwargs)

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
        out = super(PickleFileComm, cls).get_testing_options()
        out['recv'] = out['send']
        return out
        
    def _recv(self, timeout=0):
        r"""Reads message from a file.

        Args:
            timeout (float, optional): Time in seconds to wait for a message.
                Defaults to self.recv_timeout. Unused.

        Returns:
            tuple (bool, str): Success or failure of reading from the file and
                the read messages as bytes.

        """
        prev_pos = self.fd.tell()
        flag, msg = super(PickleFileComm, self)._recv(timeout=timeout)
        # Rewind file if message contains more than one pickle
        if msg != self.eof_msg:
            fd = backwards.BytesIO(msg)
            backwards.pickle.load(fd)
            used = fd.tell()
            self.fd.seek(prev_pos + used)
            msg = msg[:used]
            fd.close()
        return flag, msg
