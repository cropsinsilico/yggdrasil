from cis_interface import backwards
from cis_interface.serialize import register_serializer
from cis_interface.serialize.DefaultSerialize import DefaultSerialize


@register_serializer
class PickleSerialize(DefaultSerialize):
    r"""Class for serializing a python object into a bytes message by pickling.
    """

    _seritype = 'pickle'
    _schema_properties = dict()
    _default_type = {'type': 'bytes'}

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
        out = backwards.pickle.loads(msg)
        return out
