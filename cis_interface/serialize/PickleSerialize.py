from cis_interface import backwards
from cis_interface.serialize.DefaultSerialize import DefaultSerialize


class PickleSerialize(DefaultSerialize):
    r"""Class for serializing a python object into a bytes message by pickling.
    """
    def __init__(self, *args, **kwargs):
        super(PickleSerialize, self).__init__(*args, **kwargs)

    def __call__(self, args):
        r"""Serialize a message.

        Args:
            args (obj): Python object to be serialized.

        Returns:
            bytes, str: Serialized message.

        """
        out = backwards.pickle.dumps(args)
        return backwards.unicode2bytes(out)
