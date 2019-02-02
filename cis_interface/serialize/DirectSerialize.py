from cis_interface import backwards
from cis_interface.serialize import (
    register_serializer, _default_newline, _default_comment, format_message)
from cis_interface.serialize.DefaultSerialize import DefaultSerialize


@register_serializer
class DirectSerialize(DefaultSerialize):
    r"""Class for directly serializing bytes."""

    _seritype = 'direct'
    _schema_properties = {
        'newline': {'type': 'string',
                    'default': backwards.as_str(_default_newline)},
        'comment': {'type': 'string',
                    'default': backwards.as_str(_default_comment)}}
    _default_type = {'type': 'bytes'}

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
        return backwards.as_bytes(args)

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg: Message to be deserialized.

        Returns:
            obj: Deserialized message.

        """
        return msg

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
        # Ensure that bytes returned
        return super(DirectSerialize, cls).get_testing_options()
