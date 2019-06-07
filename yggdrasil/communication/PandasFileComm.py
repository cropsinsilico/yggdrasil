from yggdrasil.communication.AsciiTableComm import AsciiTableComm


class PandasFileComm(AsciiTableComm):
    r"""Class for handling I/O from/to a pandas csv file on disk.

    Args:
        name (str): The environment variable where communication address is
            stored.
        delimiter (str, optional): String that should be used to separate
            columns. Defaults to '\t'.
        **kwargs: Additional keywords arguments are passed to parent class.

    """

    _filetype = 'pandas'
    _schema_subtype_description = ('The file is a Pandas frame output as a table.')
    _default_serializer = 'pandas'
