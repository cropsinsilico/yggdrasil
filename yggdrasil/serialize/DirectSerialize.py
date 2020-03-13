from yggdrasil import tools
from yggdrasil.serialize import format_message
from yggdrasil.serialize.SerializeBase import SerializeBase


class DirectSerialize(SerializeBase):
    r"""Class for directly serializing bytes."""

    _seritype = 'direct'
    _schema_subtype_description = ('Direct serialization of bytes.')
    default_datatype = {'type': 'bytes'}

    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args: List of arguments to be formatted or numpy array to be
                serialized.

        Returns:
            bytes, str: Serialized message.

        """
        if (((self.extra_kwargs.get('format_str', None) is not None)
             and isinstance(args, list))):
            args = format_message(args, self.extra_kwargs['format_str'])
        return tools.str2bytes(args)

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg: Message to be deserialized.

        Returns:
            obj: Deserialized message.

        """
        return msg

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
        return [b''.join(objects)]
    
    @classmethod
    def get_testing_options(cls):
        r"""Method to return a dictionary of testing options for this class.

        Returns:
            dict: Dictionary of variables to use for testing. Key/value pairs:
                kwargs (dict): Keyword arguments for comms tested with the
                    provided content.
                empty (object): Object produced from deserializing an empty
                    message.
                objects (list): List of objects to be serialized/deserialized.
                extra_kwargs (dict): Extra keyword arguments not used to
                    construct type definition.
                typedef (dict): Type definition resulting from the supplied
                    kwargs.
                dtype (np.dtype): Numpy data types that is consistent with the
                    determined type definition.

        """
        out = {'kwargs': {}, 'empty': b'', 'dtype': None,
               'typedef': cls.default_datatype,
               'extra_kwargs': {}}
        out['objects'] = [b'Test message\n', b'Test message 2\n']
        out['contents'] = b''.join(out['objects'])
        return out
