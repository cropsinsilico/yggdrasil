from yggdrasil.communication.FileComm import FileComm


class PlyFileComm(FileComm):
    r"""Class for handling I/O from/to a .ply file on disk.

    Args:
        name (str): The environment variable where communication address is
            stored.
        **kwargs: Additional keywords arguments are passed to parent class.

    """

    _filetype = 'ply'
    _schema_subtype_description = (
        'The file is in the `Ply <http://paulbourke.net/dataformats/ply/>`_ '
        'data format for 3D structures.')
    _default_serializer = 'ply'
    _default_extension = '.ply'
