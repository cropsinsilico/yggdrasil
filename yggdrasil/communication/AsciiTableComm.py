from yggdrasil.communication.FileComm import FileComm


class AsciiTableComm(FileComm):
    r"""Class for handling I/O from/to a file on disk."""
    
    _filetype = 'table'
    _schema_subtype_description = ('The file is an ASCII table that will be '
                                   'read/written one row at a time. If '
                                   '``as_array`` is ``True``, the table will '
                                   'be read/written all at once.')
    _default_serializer = 'table'
