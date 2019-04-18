from yggdrasil.communication import FileComm


class PickleFileComm(FileComm.FileComm):
    r"""Class for handling I/O from/to a pickled file on disk.

    Args:
        name (str): The environment variable where file path is stored.
        **kwargs: Additional keywords arguments are passed to parent class.

    """

    _filetype = 'pickle'
    _schema_subtype_description = ('The file contains one or more pickled '
                                   'Python objects.')
    _default_serializer = 'pickle'
    _default_extension = '.pkl'
