from cis_interface import backwards, serialize
from cis_interface.serialize import register_serializer
from cis_interface.serialize.DefaultSerialize import DefaultSerialize


@register_serializer
class DirectSerialize(DefaultSerialize):
    r"""Class for directly serializing bytes."""

    _seritype = 'direct'
    _schema_properties = {
        'newline': {'type': 'unicode',
                    'default': backwards.bytes2unicode(serialize._default_newline)},
        'comment': {'type': 'unicode',
                    'default': backwards.bytes2unicode(serialize._default_comment)}}
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
            args = serialize.format_message(args, self.extra_kwargs['format_str'])
        return backwards.unicode2bytes(args)

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg: Message to be deserialized.

        Returns:
            obj: Deserialized message.

        """
        return msg
