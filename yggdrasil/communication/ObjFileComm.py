from yggdrasil.communication.PlyFileComm import PlyFileComm


class ObjFileComm(PlyFileComm):
    r"""Class for handling I/O from/to a .obj file on disk.

    Args:
        name (str): The environment variable where communication address is
            stored.
        **kwargs: Additional keywords arguments are passed to parent class.

    """

    _filetype = 'obj'
    _schema_subtype_description = (
        'The file is in the `Obj <http://paulbourke.net/dataformats/obj/>`_ '
        'data format for 3D structures.')
    _default_serializer = 'obj'
    _default_extension = '.obj'
