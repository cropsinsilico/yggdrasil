import json
from yggdrasil import backwards
from yggdrasil.serialize import (
    register_serializer, _default_delimiter, _default_newline)
from yggdrasil.serialize.DefaultSerialize import DefaultSerialize
from yggdrasil.metaschema.encoder import JSONReadableEncoder


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
        'delimiter': {'type': 'string',
                      'default': backwards.as_str(_default_delimiter)},
        'newline': {'type': 'string',
                    'default': backwards.as_str(_default_newline)}}
    _default_type = {'type': 'object'}

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
            if not isinstance(k, backwards.string_types):
                raise ValueError("Serialization of non-string keys not supported.")
            out += backwards.as_str(k) + self.delimiter
            if isinstance(v, backwards.string_types):
                v = backwards.as_str(v)
            out += json.dumps(v, cls=JSONReadableEncoder)
            out += self.newline
        return backwards.as_bytes(out)

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.

        Returns:
            dict: Deserialized Python dictionary.

        """
        out = dict()
        lines = (backwards.as_str(msg)).split(self.newline)
        for l in lines:
            kv = l.split(self.delimiter)
            if len(kv) <= 1:
                continue
            elif len(kv) == 2:
                if kv[1].startswith("'") and kv[1].endswith("'"):
                    out[kv[0]] = kv[1].strip("'")
                else:
                    try:
                        out[kv[0]] = json.loads(kv[1])
                    except BaseException:
                        out[kv[0]] = kv[1]
            else:
                raise ValueError("Line has more than one delimiter: " + l)
        return out

    @classmethod
    def get_testing_options(cls):
        r"""Method to return a dictionary of testing options for this class.

        Returns:
            dict: Dictionary of variables to use for testing.

        """
        out = super(AsciiMapSerialize, cls).get_testing_options()
        out['objects'] = [{'args1': int(1), 'args2': 'this',
                           # Should these be separate messages, allowing append?
                           'args3': float(1), 'args4': [int(1), int(2)]}]
        out['empty'] = dict()
        out['contents'] = (b'args1\t1\n'
                           + b'args2\t"this"\n'
                           + b'args3\t1.0\n'
                           + b'args4\t[1, 2]\n')
        return out
