import importlib
from yggdrasil import backwards
import json as stdjson
import yaml
json = stdjson
_json_encoder = stdjson.JSONEncoder
_json_decoder = stdjson.JSONDecoder
_use_rapidjson = True
if _use_rapidjson:
    try:  # pragma: Python 3
        import rapidjson as json
        _json_encoder = json.Encoder
        _json_decoder = json.Decoder
    except ImportError:  # pragma: Python 2
        _use_rapidjson = False


def indent_char2int(indent):
    r"""Convert a character indent into a number of spaces that should be used.
    Tabs are set to be equivalent to 4 spaces.

    Args:
        indent (str): String indent.

    Returns:
        int: Number of whitespaces that is equivalent to the provided string.

    """
    if isinstance(indent, str):
        indent = len(indent.replace('\t', '    '))
    return indent


def string2import(s):
    r"""Import a function/class based on its representation as a string.

    Args:
        s (str): String that may or may not contain a represetnation of an
            importable class or function.

    Returns:
        str, class, function: Imported class/function if one exists, original
            string if not.

    """
    pkg_mod = s.split(u':')
    if len(pkg_mod) == 2:
        try:
            mod = importlib.import_module(pkg_mod[0])
            s = getattr(mod, pkg_mod[1])
        except (ImportError, AttributeError):
            pass
    return s


class JSONReadableEncoder(stdjson.JSONEncoder):
    r"""Encoder class for Ygg messages."""

    def default(self, o):  # pragma: no cover
        r"""Encoder that allows for expansion types."""
        from yggdrasil.metaschema.datatypes import (
            encode_data_readable, MetaschemaTypeError)
        try:
            return encode_data_readable(o)
        except MetaschemaTypeError:
            if _use_rapidjson:
                raise TypeError("Cannot encode %s" % o)
            else:
                return _json_encoder.default(self, o)


class JSONEncoder(_json_encoder):
    r"""Encoder class for Ygg messages."""

    def default(self, o):
        r"""Encoder that allows for expansion types."""
        from yggdrasil.metaschema.datatypes import (
            encode_data, MetaschemaTypeError)
        try:
            return encode_data(o)
        except MetaschemaTypeError:
            if _use_rapidjson:
                raise TypeError("Cannot encode %s" % o)
            else:
                return _json_encoder.default(self, o)
    

class JSONDecoder(_json_decoder):
    r"""Decoder class for Ygg messages."""

    def __init__(self, *args, **kwargs):
        super(JSONDecoder, self).__init__(*args, **kwargs)
        if not _use_rapidjson:
            from json.scanner import py_make_scanner
            self.scan_once = py_make_scanner(self)

    def string(self, s):
        r"""Try to parse string with class."""
        # TODO: Do this dynamically for classes based on an attribute
        return string2import(s)

    @property
    def parse_string(self):
        r"""function: Wrapper for function that parses strings."""
        def parse_string_ygg(*args, **kwargs):
            out, end = self._parse_string(*args, **kwargs)
            return self.string(out), end
        return parse_string_ygg

    @parse_string.setter
    def parse_string(self, x):
        self._parse_string = x

    # @property
    # def scan_once(self):
    #     r"""function: Wrapper for function that decodes JSON documents."""
    #     def scan_once_ygg(string, idx):
    #         try:
    #             if string[idx] == '"':
    #                 return self.parse_string(string, idx + 1, self.encoding,
    #                                          self.strict)
    #         except IndexError:
    #             pass
    #         return self._scan_once(string, idx)
    #     return scan_once_ygg

    # @scan_once.setter
    # def scan_once(self, x):
    #     self._scan_once = x

    
def encode_json(obj, fd=None, indent=None, sort_keys=True, **kwargs):
    r"""Encode a Python object in JSON format.

    Args:
        obj (object): Python object to encode.
        fd (file, optional): File descriptor for file that encoded object
            should be written to. Defaults to None and string is returned.
        indent (int, str, optional): Indentation for new lines in encoded
            string. Defaults to None.
        sort_keys (bool, optional): If True, the keys will be output in sorted
            order. Defaults to True.
        **kwargs: Additional keyword arguments are passed to json.dumps.

    Returns:
        str, bytes: Encoded object.

    """
    if (indent is None) and (fd is not None):
        indent = '\t'
    if backwards.PY2 or _use_rapidjson:  # pragma: Python 2
        # Character indents not allowed in Python 2 json
        indent = indent_char2int(indent)
    kwargs['indent'] = indent
    kwargs['sort_keys'] = sort_keys
    if _use_rapidjson:
        kwargs.setdefault('default', JSONEncoder().default)
    else:
        kwargs.setdefault('cls', JSONEncoder)
    if fd is None:
        return backwards.as_bytes(json.dumps(obj, **kwargs))
    else:
        return json.dump(obj, fd, **kwargs)


def decode_json(msg, **kwargs):
    r"""Decode a Python object from a JSON serialization.

    Args:
        msg (str): JSON serialization to decode.
        **kwargs: Additional keyword arguments are passed to json.loads.

    Returns:
        object: Deserialized Python object.

    """
    if isinstance(msg, backwards.string_types):
        # Should this be unicode?
        msg_decode = backwards.as_str(msg)
        func_decode = json.loads
    else:
        msg_decode = msg
        func_decode = json.load
    if _use_rapidjson:
        func_decode = JSONDecoder()
    else:
        kwargs.setdefault('cls', JSONDecoder)
    return func_decode(msg_decode, **kwargs)


def encode_yaml(obj, fd=None, indent=None,
                sorted_dict_type=None, **kwargs):
    r"""Encode a Python object in YAML format.

    Args:
        obj (object): Python object to encode.
        fd (file, optional): File descriptor for file that encoded object
            should be written to. Defaults to None and string is returned.
        indent (int, str, optional): Indentation for new lines in encoded
            string. Defaults to None.
        **kwargs: Additional keyword arguments are passed to yaml.dump.

    Returns:
        str, bytes: Encoded object.

    """
    from yggdrasil.metaschema.datatypes import encode_data_readable
    if (indent is None) and (fd is not None):
        indent = '\t'
    indent = indent_char2int(indent)
    kwargs['indent'] = indent
    if fd is not None:
        assert('stream' not in kwargs)
        kwargs['stream'] = fd
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
    return yaml.dump(encode_data_readable(obj), **kwargs)


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

    def construct_scalar(loader, node):
        out = loader.construct_scalar(node)
        out = string2import(out)
        return out

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_SCALAR_TAG,
        construct_scalar)
    kwargs['Loader'] = OrderedLoader
    out = yaml.load(msg, **kwargs)
    # out = backwards.as_str(out, recurse=True, allow_pass=True)
    return out
