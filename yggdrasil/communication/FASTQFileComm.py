from yggdrasil.communication.SequenceFileComm import BioPythonFileBase


class FASTQFileComm(BioPythonFileBase):
    r"""Class for I/O from/to FASTQ sequence files."""

    _filetype = 'fastq'
    _valid_fields = BioPythonFileBase._valid_fields + [
        'letter_annotations']
