import yaml
from yggdrasil import rapidjson
from yggdrasil.serialize.JSONSerialize import (
    JSONSerialize, indent_char2int)


def encode_yaml(obj, fd=None, indent=None,
                sorted_dict_type=None, sort_keys=True, **kwargs):
    r"""Encode a Python object in YAML format.

    Args:
        obj (object): Python object to encode.
        fd (file, optional): File descriptor for file that encoded object
            should be written to. Defaults to None and string is returned.
        indent (int, str, optional): Indentation for new lines in encoded
            string. Defaults to None.
        sort_keys (bool, optional): If True, dictionaries will be sorted
            alphabetically by key. Defaults to True.
        **kwargs: Additional keyword arguments are passed to yaml.dump.

    Returns:
        str, bytes: Encoded object.

    """
    if (indent is None) and (fd is not None):
        indent = '\t'
    indent = indent_char2int(indent)
    kwargs['indent'] = indent
    if fd is not None:
        assert 'stream' not in kwargs
        kwargs['stream'] = fd
    json_kws = {}
    if sorted_dict_type is not None:
        class OrderedDumper(kwargs.get('Dumper', yaml.SafeDumper)):
            pass
        
        def _dict_representer(dumper, data):
            return dumper.represent_mapping(
                yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                data.items())

        if not isinstance(sorted_dict_type, list):
            sorted_dict_type = [sorted_dict_type]
        for x in sorted_dict_type:
            OrderedDumper.add_representer(x, _dict_representer)
        kwargs['Dumper'] = OrderedDumper
        
        class OrderedDecoder(rapidjson.Decoder):
            def start_object(self):
                return sorted_dict_type[0]()
        json_kws['decoder'] = OrderedDecoder()
        if sort_keys:
            json_kws['mapping_mode'] = rapidjson.MM_SORT_KEYS
    
    obj = rapidjson.as_pure_json(obj, **json_kws)
    return yaml.dump(obj, sort_keys=sort_keys, **kwargs)


def decode_yaml(msg, sorted_dict_type=None, **kwargs):
    r"""Decode a Python object from a YAML serialization.

    Args:
        msg (str): YAML serialization to decode.
        sorted_dict_type (type, optional): Class that should be used to
            contain mapping objects while preserving order. Defaults to
            None and is ignored.
        **kwargs: Additional keyword arguments are passed to yaml.load.

    Returns:
        object: Deserialized Python object.

    """
    class OrderedLoader(kwargs.get('Loader', yaml.Loader)):
        pass

    if sorted_dict_type is not None:
        def construct_mapping(loader, node):
            loader.flatten_mapping(node)
            return sorted_dict_type(loader.construct_pairs(node))

        OrderedLoader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            construct_mapping)

    # If this is required, add a method to rapidjson python wrapper
    # def construct_scalar(loader, node):
    #     out = loader.construct_scalar(node)
    #     out = string2import(out)
    #     return out

    # OrderedLoader.add_constructor(
    #     yaml.resolver.BaseResolver.DEFAULT_SCALAR_TAG,
    #     construct_scalar)
    kwargs['Loader'] = OrderedLoader
    out = yaml.load(msg, **kwargs)
    return out


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
    file_extensions = ['.yaml', '.yml']

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
               'datatype': {'type': 'object'}}
        out['contents'] = (b'a:\n- b\n- 1\n- 1.0\n'
                           b'c:\n    z: hello\n'
                           b'd: new field\n')
        # out['contents'] = (b'-   a:\n    - b\n    - 1\n    - 1.0\n'
        #                    b'    c:\n        z: hello\n'
        #                    b'    d: new field\n'
        #                    b'- 2\n- 2.0\n')
        return out
