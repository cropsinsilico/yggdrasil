from yggdrasil.communication import FileComm


class WOFOSTParamFileComm(FileComm.FileComm):
    r"""Class for handling I/O from/to a WOFOST parameter file on disk."""

    _filetype = 'wofost'
    _schema_subtype_description = 'The file is a WOFOST parameter file.'
    _default_serializer = 'wofost'
