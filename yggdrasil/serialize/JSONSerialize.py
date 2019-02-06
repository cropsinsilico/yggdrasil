from yggdrasil import backwards
from yggdrasil.metaschema.encoder import (
    indent_char2int, encode_json, decode_json, _use_rapidjson)
from yggdrasil.serialize import register_serializer
from yggdrasil.serialize.DefaultSerialize import DefaultSerialize


@register_serializer
class JSONSerialize(DefaultSerialize):
    r"""Class for serializing a python object into a bytes message using JSON."""

    _seritype = 'json'
    _schema_properties = dict(
        DefaultSerialize._schema_properties,
        indent={'type': ['string', 'int'], 'default': '\t'},
        sort_keys={'type': 'boolean', 'default': True})
    _default_type = {'type': 'object'}

    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args (obj): Python object to be serialized.

        Returns:
            bytes, str: Serialized message.

        """
        # Convert bytes to str because JSON cannot serialize bytes by default
        args = backwards.as_str(args, recurse=True, allow_pass=True)
        return encode_json(args, indent=self.indent)

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.

        Returns:
            obj: Deserialized Python object.

        """
        return decode_json(msg)

    @classmethod
    def get_testing_options(cls, **kwargs):
        r"""Method to return a dictionary of testing options for this class.

        Returns:
            dict: Dictionary of variables to use for testing.

        """
        iobj = {'a': ['b', int(1), float(1.0)], 'c': {'z': 'hello'}}
        out = {'kwargs': {},
               'empty': {}, 'dtype': None,
               'extra_kwargs': {},
               'objects': [iobj],
               'typedef': {'type': 'object'}}
        out['contents'] = (b'{\n\t"a": [\n\t\t"b",\n\t\t1,\n\t\t1.0\n\t],'
                           b'\n\t"c": {\n\t\t"z": "hello"\n\t}\n}')
        if backwards.PY2 or _use_rapidjson:  # pragma: Python 2
            tab_rep = indent_char2int('\t') * b' '
            out['contents'] = out['contents'].replace(b'\t', tab_rep)
        if backwards.PY2:  # pragma: Python 2
            out['contents'] = out['contents'].replace(b',', b', ')
        return out
