from yggdrasil.communication import FileComm


class JSONFileComm(FileComm.FileComm):
    r"""Class for handling I/O from/to a JSON file on disk.

    Args:
        name (str): The environment variable where file path is stored.
        **kwargs: Additional keywords arguments are passed to parent class.

    """

    _filetype = 'json'
    _schema_subtype_description = ('The file contains a JSON serialized object.')
    _default_serializer = 'json'
