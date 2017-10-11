import os
from cis_interface.serialize import PickleSerialize, PickleDeserialize
from cis_interface.communication import FileComm


class PickleFileComm(FileComm.FileComm):
    r"""Class for handling I/O from/to a pickled file on disk.

    Args:
        name (str): The environment variable where file path is stored.
        **kwargs: Additional keywords arguments are passed to parent class.

    """
    def __init__(self, name, **kwargs):
        kwargs.setdefault('readmeth', 'read')
        super(PickleFileComm, self).__init__(name, **kwargs)
        self.meth_serialize = PickleSerialize.PickleSerialize()
        self.meth_deserialize = PickleDeserialize.PickleDeserialize()
