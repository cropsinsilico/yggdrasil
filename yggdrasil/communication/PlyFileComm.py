from yggdrasil.communication.FileComm import FileComm
from yggdrasil.schema import register_component
from yggdrasil.serialize.PlySerialize import PlySerialize


@register_component
class PlyFileComm(FileComm):
    r"""Class for handling I/O from/to a .ply file on disk.

    Args:
        name (str): The environment variable where communication address is
            stored.
        **kwargs: Additional keywords arguments are passed to parent class.

    """

    _filetype = 'ply'
    _default_serializer = PlySerialize
    _default_extension = '.ply'

    def _init_before_open(self, **kwargs):
        super(PlyFileComm, self)._init_before_open(**kwargs)
        self.read_meth = 'read'
        if self.append:
            self.append = 'ow'

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
        out = super(PlyFileComm, cls).get_testing_options()
        obj = out['send'][0]
        for x in out['send'][1:]:
            obj = obj.merge(x)
        out['recv'] = [obj]
        return out
    
    def _send(self, msg):
        r"""Write message to a file. Merging existing ply info as needed.

        Args:
            msg (bytes, str): Data to write to the file.

        Returns:
            bool: Success or failure of writing to the file.

        """
        if (msg != self.eof_msg) and (self.fd.tell() != 0):
            self.fd.seek(0)
            msg_ply, header = self.deserialize(msg)
            with open(self.current_address, 'rb') as fd:
                old_ply, header = self.deserialize(fd.read())
            old_ply.append(msg_ply)
            new_msg = self.serialize(old_ply)
        else:
            new_msg = msg
        return super(PlyFileComm, self)._send(new_msg)
