from cis_interface.communication.PlyFileComm import PlyFileComm
from cis_interface.schema import register_component
from cis_interface.serialize.ObjSerialize import ObjSerialize


@register_component
class ObjFileComm(PlyFileComm):
    r"""Class for handling I/O from/to a .obj file on disk.

    Args:
        name (str): The environment variable where communication address is
            stored.
        **kwargs: Additional keywords arguments are passed to parent class.

    """

    _filetype = 'obj'
    _default_serializer = ObjSerialize
    _default_extension = '.obj'

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
        out = super(ObjFileComm, cls).get_testing_options()
        obj = out['send'][0]
        for x in out['send'][1:]:
            obj = obj.merge(x)
        out['recv'] = [obj]
        return out
