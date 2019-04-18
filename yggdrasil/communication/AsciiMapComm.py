from yggdrasil.communication import FileComm


class AsciiMapComm(FileComm.FileComm):
    r"""Class for handling I/O from/to a ASCII map on disk.

    Args:
        name (str): The environment variable where file path is stored.
        **kwargs: Additional keywords arguments are passed to parent class.

    """

    _filetype = 'map'
    _schema_subtype_description = ('The file contains a key/value mapping '
                                   'with one key/value pair per line and '
                                   'separated by some delimiter.')
    _default_serializer = 'map'
