import yaml
from yggdrasil.metaschema.encoder import indent_char2int
from yggdrasil.serialize.JSONSerialize import JSONSerialize


class YAMLSerialize(JSONSerialize):
    r"""Class for serializing a python object into a bytes message using YAML.

    Args:
        indent (str, int, optional): String or number of spaces that should be
            used to indent each level within the seiralized structure. Defaults
            to '\t'.
        encoding (str, optional): Encoding that should be used to serialize the
            object. Defaults to 'utf-8'.
        default_flow_style (bool, optional): If True, nested collections will
            be serialized in the block style. If False, they will always be
            serialized in the flow style. See
            `PyYAML Documentation <https://pyyaml.org/wiki/PyYAMLDocumentation>`_.

    """

    _seritype = 'yaml'
    _schema_subtype_description = ('Serializes Python objects using the YAML '
                                   'standard.')
    _schema_properties = {
        'indent': {'type': ['string', 'int'], 'default': '\t'},
        'encoding': {'type': 'string', 'default': 'utf-8'},
        'default_flow_style': {'type': 'boolean', 'default': False}}
    _schema_excluded_from_inherit = ['sort_keys']

    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args (obj): Python object to be serialized.

        Returns:
            bytes, str: Serialized message.

        """
        # Convert objects to built-in python types where possible for
        # readable encoding
        args = self.datatype.encode_data_readable(args, None)
        # args = backwards.as_str(args, recurse=True, allow_pass=True)
        # Convert character indent to an integer (tabs are 4 spaces)
        indent = indent_char2int(self.indent)
        out = yaml.dump(args, indent=indent, encoding=self.encoding,
                        default_flow_style=self.default_flow_style)
        return out

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.

        Returns:
            obj: Deserialized Python object.

        """
        out = yaml.safe_load(msg)
        return out

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
        out['contents'] = b'a:\n- b\n- 1\n- 1.0\nc:\n    z: hello\n'
        return out
