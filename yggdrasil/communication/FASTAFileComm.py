from yggdrasil.communication.SequenceFileComm import BioPythonFileBase


class FASTAFileComm(BioPythonFileBase):
    r"""Class for I/O from/to FASTA sequence files."""

    _filetype = 'fasta'
