import numpy as np
from yggdrasil import serialize, rapidjson
from yggdrasil.serialize.SerializeBase import SerializeBase


class DefaultSerialize(SerializeBase):
    r"""Default class for serializing/deserializing a python object into/from
    a bytes message.

    Args:
        **kwargs: Additional keyword args are passed to the parent class.

    """

    _seritype = 'default'
    _schema_subtype_description = ('Default serializer that uses |yggdrasil|\'s '
                                   'extended JSON serialization based on a '
                                   'provided type definition (See discussion '
                                   ':ref:`here <serialization_rst>`).')
    file_extensions = ['.ygg']
    
    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args: List of arguments to be formatted or numpy array to be
                serialized.

        Returns:
            bytes, str: Serialized message.

        """
        return rapidjson.dumps(args).encode('utf8')

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg: Message to be deserialized.

        Returns:
            obj: Deserialized message.

        """
        return rapidjson.loads(msg.decode('utf8'))
    
    @classmethod
    def dict2object(cls, obj, as_array=False, field_names=None, **kwargs):
        r"""Conver a dictionary to a message object.

        Args:
            obj (dict): Dictionary to convert to serializable object.
            as_array (bool, optional): If True, the objects in the list
                are complete columns in a table and as_format is set to True.
                Defaults to False.
            field_names (list, optional): The field names associated with a
                table-like data type. Defaults to None. This keyword must be
                provided if as_array is True.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            object: Serializable object.

        """
        if field_names is None and len(obj) == 1:
            assert not as_array
            return super(DefaultSerialize, cls).dict2object(obj, **kwargs)
        return serialize.dict2list(obj, order=field_names)

    @classmethod
    def object2dict(cls, obj, as_array=False, field_names=None, **kwargs):
        r"""Convert a message object into a dictionary.

        Args:
            obj (object): Object that would be serialized by this class and
                should be returned in a dictionary form.
            as_array (bool, optional): If True, the objects in the list
                are complete columns in a table and as_format is set to True.
                Defaults to False.
            field_names (list, optional): The field names associated with a
                table-like data type. Defaults to None. This keyword must be
                provided if as_array is True.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            dict: Dictionary version of the provided object.

        """
        if field_names is None:
            assert not as_array
            return super(DefaultSerialize, cls).object2dict(obj, **kwargs)
        if len(field_names) == 1 and not isinstance(obj, (list, tuple)):
            return {field_names[0]: obj}
        if isinstance(obj, np.ndarray):
            return serialize.numpy2dict(obj)
        return serialize.list2dict(obj, names=field_names)

    @classmethod
    def object2array(cls, obj, as_array=False, field_names=None, **kwargs):
        r"""Convert a message object into an array.

        Args:
            obj (object): Object that would be serialized by this class and
                should be returned in an array form.
            as_array (bool, optional): If True, the objects in the list
                are complete columns in a table and as_format is set to True.
                Defaults to False.
            field_names (list, optional): The field names associated with a
                table-like data type. Defaults to None. This keyword must be
                provided if as_array is True.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            np.array: Array version of the provided object.

        """
        if as_array and not isinstance(obj, np.ndarray):
            assert field_names is not None
            return serialize.list2numpy(obj, names=field_names)
        return super(DefaultSerialize, cls).object2array(obj, **kwargs)

    @classmethod
    def concatenate(cls, objects, as_array=False, **kwargs):
        r"""Concatenate objects to get object that would be recieved if
        the concatenated serialization were deserialized.

        Args:
            objects (list): Objects to be concatenated.
            as_array (bool, optional): If True, the objects in the list
                are complete columns in a table and as_format is set to True.
                Defaults to False.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            list: Set of objects that results from concatenating those provided.

        """
        if len(objects) == 0:
            return []
        if as_array:
            out = [[np.hstack([x[i] for x in objects])
                    for i in range(len(objects[0]))]]
        elif isinstance(objects[0], bytes):
            out = [b''.join(objects)]
        else:
            return super(DefaultSerialize, cls).concatenate(objects, **kwargs)
        return out

    @classmethod
    def get_testing_options(cls, **kwargs):
        r"""Method to return a dictionary of testing options for this class."""
        out = super(DefaultSerialize, cls).get_testing_options(**kwargs)
        if cls._seritype == 'default':
            out['concatenate'] = [([], []),
                                  ([b'a', b'b'], [b'ab'])]
        return out
