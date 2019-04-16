from yggdrasil.communication import FileComm


class MatFileComm(FileComm.FileComm):
    r"""Class for handling I/O from/to a Matlab .mat file on disk.

    Args:
        name (str): The environment variable where file path is stored.
        **kwargs: Additional keywords arguments are passed to parent class.

    """

    _filetype = 'mat'
    _schema_subtype_description = ('The file is a Matlab .mat file containing '
                                   'one or more serialized Matlab variables.')
    _default_serializer = 'mat'
    _default_extension = '.mat'
