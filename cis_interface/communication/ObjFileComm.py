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
