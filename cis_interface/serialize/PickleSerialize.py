from cis_interface import backwards
from cis_interface.serialize.DefaultSerialize import DefaultSerialize


class PickleSerialize(DefaultSerialize):
    r"""Class for serializing a python object into a bytes message by pickling.
    """

    @property
    def serializer_type(self):
        r"""int: Type of serializer."""
        return 4
        
    @property
    def empty_msg(self):
        r"""obj: Object indicating empty message."""
        return backwards.unicode2bytes('')
            
    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args (obj): Python object to be serialized.

        Returns:
            bytes, str: Serialized message.

        """
        out = backwards.pickle.dumps(args)
        return backwards.unicode2bytes(out)

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.

        Returns:
            obj: Deserialized Python object.

        """
        if len(msg) == 0:
            out = self.empty_msg
        else:
            out = backwards.pickle.loads(msg)
        return out
