from scipy.io import loadmat
from cis_interface import backwards
from cis_interface.serialize.DefaultDeserialize import DefaultDeserialize


class MatDeserialize(DefaultDeserialize):
    r"""Class for deserializing a python object from a bytes message using
    Matlab .mat style."""
    
    def __init__(self, *args, **kwargs):
        super(MatDeserialize, self).__init__(*args, **kwargs)

    def __call__(self, msg):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.

        Returns:
            obj: Deserialized Python object.

        """
        if len(msg) == 0:
            return ''
        fd = backwards.sio.StringIO(msg)
        out = loadmat(fd, squeeze_me=False)
        mat_keys = ['__header__', '__globals__', '__version__']
        for k in mat_keys:
            del out[k]
        fd.close()
        return out
