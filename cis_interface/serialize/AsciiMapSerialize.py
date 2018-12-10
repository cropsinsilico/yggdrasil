import json
from cis_interface import backwards, serialize
from cis_interface.serialize import register_serializer
from cis_interface.serialize.DefaultSerialize import DefaultSerialize
from cis_interface.metaschema.encoder import JSONReadableEncoder


@register_serializer
class AsciiMapSerialize(DefaultSerialize):
    r"""Class for serializing/deserializing name/value mapping.

    Args:
        delimiter (str, optional): Delimiter that should be used to
            separate name/value pairs in the map. Defaults to \t.
        newline (str, optional): Delimiter that should be used to
            separate lines. Defaults to \n.

    """
    
    _seritype = 'ascii_map'
    _schema_properties = {
        'delimiter': {'type': 'unicode',
                      'default': backwards.bytes2unicode(serialize._default_delimiter)},
        'newline': {'type': 'unicode',
                    'default': backwards.bytes2unicode(serialize._default_newline)}}
    _default_type = {'type': 'object'}

    @property
    def empty_msg(self):
        r"""obj: Object indicating empty message."""
        return dict()

    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args (dict): Python dictionary to be serialized.

        Returns:
            bytes, str: Serialized message.

        """
        out = ''
        order = sorted([k for k in args.keys()])
        for k in order:
            v = args[k]
            if not isinstance(k, str):
                raise ValueError("Serialization of non-string keys not supported.")
            out += k + self.delimiter
            if isinstance(v, backwards.string_types):
                v = backwards.bytes2unicode(v)
            out += json.dumps(v, cls=JSONReadableEncoder)
            out += self.newline
        return backwards.unicode2bytes(out)

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.

        Returns:
            dict: Deserialized Python dictionary.

        """
        if len(msg) == 0:
            out = self.empty_msg
        else:
            out = dict()
            lines = backwards.bytes2unicode(msg).split(self.newline)
            for l in lines:
                kv = l.split(self.delimiter)
                if len(kv) <= 1:
                    continue
                elif len(kv) == 2:
                    if kv[1].startswith("'") and kv[1].endswith("'"):
                        out[kv[0]] = kv[1].strip("'")
                    else:
                        out[kv[0]] = json.loads(kv[1])
                else:
                    raise ValueError("Line has more than one delimiter: " + l)
        return out
