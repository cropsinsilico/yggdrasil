from yggdrasil.communication import FileComm


class YAMLFileComm(FileComm.FileComm):
    r"""Class for handling I/O from/to a YAML file on disk.

    Args:
        name (str): The environment variable where file path is stored.
        **kwargs: Additional keywords arguments are passed to parent class.

    """

    _filetype = 'yaml'
    _schema_subtype_description = ('The file contains a YAML serialized object.')
    _default_serializer = 'yaml'
