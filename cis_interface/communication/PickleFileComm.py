from cis_interface import backwards
from cis_interface.communication import FileComm
from cis_interface.schema import register_component


@register_component
class PickleFileComm(FileComm.FileComm):
    r"""Class for handling I/O from/to a pickled file on disk.

    Args:
        name (str): The environment variable where file path is stored.
        **kwargs: Additional keywords arguments are passed to parent class.

    """

    _filetype = 'pickle'

    def __init__(self, name, **kwargs):
        kwargs.setdefault('readmeth', 'read')
        kwargs['serializer_kwargs'] = dict(stype=4)
        super(PickleFileComm, self).__init__(name, **kwargs)

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
