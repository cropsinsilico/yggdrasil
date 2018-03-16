from scipy.io import savemat, loadmat
from cis_interface import backwards
from cis_interface.serialize.DefaultSerialize import DefaultSerialize


class MatSerialize(DefaultSerialize):
    r"""Class for serializing a python object into a bytes message using the
    Matlab .mat format."""
    
    @property
    def serializer_type(self):
        r"""int: Type of serializer."""
        return 5
        
    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args (obj): Python object to be serialized.

        Returns:
            bytes, str: Serialized message.

        Raises:
            TypeError: If args is not a dictionary.

        """
        if isinstance(args, backwards.bytes_type) and (len(args) == 0):
            return args
        if not isinstance(args, dict):
            raise TypeError('Object (type %s) is not a dictionary' %
                            type(args))
        fd = backwards.BytesIO()
        savemat(fd, args)
        out = fd.getvalue()
        fd.close()
        return out

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.

        Returns:
            obj: Deserialized Python object.

        """
        if len(msg) == 0:
            return dict()
        fd = backwards.BytesIO(msg)
        out = loadmat(fd, squeeze_me=False)
        mat_keys = ['__header__', '__globals__', '__version__']
        for k in mat_keys:
            del out[k]
        fd.close()
        return out
