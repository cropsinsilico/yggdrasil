import io as sio
import numpy as np
from scipy.io import savemat, loadmat
from yggdrasil import platform
from yggdrasil.serialize.SerializeBase import SerializeBase


class MatSerialize(SerializeBase):
    r"""Class for serializing a python object into a bytes message using the
    Matlab .mat format."""
    
    _seritype = 'mat'
    _schema_subtype_description = ('Serializes objects using the Matlab .mat '
                                   'format.')
    default_datatype = {'type': 'object'}
    concats_as_str = False

    def func_serialize(self, args):
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
        fd = sio.BytesIO()
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
        fd = sio.BytesIO(msg)
        out = loadmat(fd, matlab_compatible=True)
        mat_keys = ['__header__', '__globals__', '__version__']
        for k in mat_keys:
            del out[k]
        fd.close()
        return out

    @classmethod
    def concatenate(cls, objects, **kwargs):
        r"""Concatenate objects to get object that would be recieved if
        the concatenated serialization were deserialized.

        Args:
            objects (list): Objects to be concatenated.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            list: Set of objects that results from concatenating those provided.

        """
        total = {}
        for x in objects:
            total.update(x)
        return [total]
        
    @classmethod
    def get_testing_options(cls):
        r"""Method to return a dictionary of testing options for this class.

        Returns:
            dict: Dictionary of variables to use for testing.

        """
        # msg = {'a': np.array([[int(1)]]), 'b': np.array([[float(1)]])}
        msg1 = {'a': np.array([[int(1)]]), 'b': np.array([[float(1)]])}
        msg2 = {'c': np.array([[int(1)]]), 'd': np.array([[float(1)]])}
        out = super(MatSerialize, cls).get_testing_options()
        out['objects'] = [msg1, msg2]
        out['empty'] = dict()
        out['contents'] = cls().func_serialize(cls.concatenate(out['objects'])[0])
        out['contents'] = out['contents'].replace(b'\n', platform._newline)
        out['exact_contents'] = False  # Contains a time stamp
        return out
