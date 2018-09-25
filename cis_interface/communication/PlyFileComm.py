from cis_interface.communication.FileComm import FileComm
from cis_interface.schema import register_component


@register_component
class PlyFileComm(FileComm):
    r"""Class for handling I/O from/to a .ply file on disk.

    Args:
        name (str): The environment variable where communication address is
            stored.
        **kwargs: Additional keywords arguments are passed to parent class.

    """

    _filetype = 'ply'

    def _init_before_open(self, serializer_kwargs=None, **kwargs):
        if serializer_kwargs is None:
            serializer_kwargs = {}
        serializer_kwargs.setdefault('stype', 8)
        kwargs['serializer_kwargs'] = serializer_kwargs
        super(PlyFileComm, self)._init_before_open(**kwargs)
        self.read_meth = 'read'
        if self.append:
            self.append = 'ow'

    def _send(self, msg):
        r"""Write message to a file. Merging existing ply info as needed.

        Args:
            msg (bytes, str): Data to write to the file.

        Returns:
            bool: Success or failure of writing to the file.

        """
        if (msg != self.eof_msg) and (self.fd.tell() != 0):
            self.fd.seek(0)
            msg_ply, header = self.serializer.deserialize(msg)
            with open(self.current_address, 'rb') as fd:
                old_ply, header = self.serializer.deserialize(fd.read())
            old_ply.append(msg_ply)
            new_msg = self.serializer.serialize(old_ply)
        else:
            new_msg = msg
        return super(PlyFileComm, self)._send(new_msg)
