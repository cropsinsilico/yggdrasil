from cis_interface import backwards
from cis_interface.serialize.DefaultSerialize import DefaultSerialize


class PickleSerialize(DefaultSerialize):
    r"""Class for serializing a python object into a bytes message by pickling.
    """

    def serialize(self, args):
        r"""Serialize a message.

        Args:
            args (obj): Python object to be serialized.

        Returns:
            bytes, str: Serialized message.

        """
        out = backwards.pickle.dumps(args)
        return backwards.unicode2bytes(out)

    def deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.

        Returns:
            obj: Deserialized Python object.

        """
        if len(msg) == 0:
            out = msg
        else:
            out = backwards.pickle.loads(msg)
        return out
