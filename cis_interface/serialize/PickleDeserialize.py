from cis_interface import backwards
from cis_interface.serialize.DefaultDeserialize import DefaultDeserialize


class PickleDeserialize(DefaultDeserialize):
    r"""Class for deserializing a python object from a bytes message by
    pickling."""
    
    def __init__(self, *args, **kwargs):
        super(PickleDeserialize, self).__init__(*args, **kwargs)

    def __call__(self, msg):
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
