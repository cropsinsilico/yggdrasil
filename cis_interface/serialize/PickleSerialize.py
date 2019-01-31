from cis_interface import backwards  # , platform
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
        return backwards.as_bytes(out)

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.

        Returns:
            obj: Deserialized Python object.

        """
        out = backwards.pickle.loads(msg)
        return out

    @classmethod
    def get_testing_options(cls, **kwargs):
        r"""Method to return a dictionary of testing options for this class.

        Returns:
            dict: Dictionary of variables to use for testing.

        """
        out = super(PickleSerialize, cls).get_testing_options()
        if backwards.PY2:  # pragma: Python 2
            out['contents'] = ("S'Test message\\n'\np1\n."
                               + "S'Test message 2\\n'\np1\n.")
        else:  # pragma: Python 3
            out['contents'] = (b'\x80\x03C\rTest message\nq\x00.'
                               + b'\x80\x03C\x0fTest message 2\nq\x00.')
        return out
