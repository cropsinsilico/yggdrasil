from yggdrasil.metaschema.encoder import encode_yaml, decode_yaml
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
        return encode_yaml(args, indent=self.indent, encoding=self.encoding,
                           default_flow_style=self.default_flow_style)

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.

        Returns:
            obj: Deserialized Python object.

        """
        return decode_yaml(msg)

    @classmethod
    def get_testing_options(cls, **kwargs):
        r"""Method to return a dictionary of testing options for this class.

        Returns:
            dict: Dictionary of variables to use for testing.

        """
        # iobj = {'a': ['b', int(1), float(1.0)], 'c': {'z': 'hello'}}
        iobj1 = {'a': ['b', int(1), float(1.0)], 'c': {'z': 'hello'}}
        iobj2 = {'d': 'new field'}
        # iobj3 = int(2)
        # iobj4 = [float(2.0)]
        out = {'kwargs': {},
               'empty': {}, 'dtype': None,
               'extra_kwargs': {},
               'objects': [iobj1, iobj2],  # , iobj3, iobj4],
               'typedef': {'type': 'object'}}
        out['contents'] = (b'a:\n- b\n- 1\n- 1.0\n'
                           b'c:\n    z: hello\n'
                           b'd: new field\n')
        # out['contents'] = (b'-   a:\n    - b\n    - 1\n    - 1.0\n'
        #                    b'    c:\n        z: hello\n'
        #                    b'    d: new field\n'
        #                    b'- 2\n- 2.0\n')
        return out
