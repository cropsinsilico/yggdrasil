from yggdrasil.communication import FileComm


class CABOFileComm(FileComm.FileComm):
    r"""Class for handling I/O from/to a CABO parameter file on disk."""

    _filetype = 'cabo'
    _schema_subtype_description = 'The file is a CABO parameter file.'
    _default_serializer = 'cabo'
    _deprecated_drivers = []
