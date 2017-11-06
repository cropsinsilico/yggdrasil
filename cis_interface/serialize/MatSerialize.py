from scipy.io import savemat
from cis_interface import backwards
from cis_interface.serialize.DefaultSerialize import DefaultSerialize


class MatSerialize(DefaultSerialize):
    r"""Class for serializing a python object into a bytes message using the
    Matlab .mat format."""
    
    def __init__(self, *args, **kwargs):
        super(MatSerialize, self).__init__(*args, **kwargs)

    def __call__(self, args):
        r"""Serialize a message.

        Args:
            args (obj): Python object to be serialized.

        Returns:
            bytes, str: Serialized message.

        Raises:
            TypeError: If args is not a dictionary.

        """
        if not isinstance(args, dict):
            raise TypeError('Object (type %s) is not a dictionary' %
                            type(args))
        fd = backwards.BytesIO()
        savemat(fd, args)
        out = fd.getvalue()
        fd.close()
        return out
