import numpy as np
from yggdrasil import units, serialize
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
    func_serialize = None
    func_deserialize = None
    
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
            assert(not as_array)
            return super(DefaultSerialize, cls).object2dict(obj, **kwargs)
        else:
            out = serialize.list2dict(obj, names=field_names)
        return out

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
        if as_array:
            assert(field_names is not None)
            out = serialize.list2numpy(obj, names=field_names)
        else:
            out = super(DefaultSerialize, cls).object2array(obj, **kwargs)
        return out

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
            units_list = [units.get_units(ix) for ix in objects[0]]
            out = [[units.add_units(np.hstack([x[i] for x in objects]), u)
                    for i, u in enumerate(units_list)]]
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
        
    def update_serializer(self, *args, **kwargs):
        r"""Update serializer with provided information.

        Args:
            *args: All arguments are passed to the parent class's method.
            **kwargs: All keyword arguments are passed to the parent class's
                method.

        """
        out = super(DefaultSerialize, self).update_serializer(*args, **kwargs)
        if (self.func_serialize is None) or (self.func_deserialize is None):
            self.encoded_datatype = self.datatype
        return out
