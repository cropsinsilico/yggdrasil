from yggdrasil import backwards
import json as stdjson
json = stdjson
_use_rapidjson = True
if _use_rapidjson:
    try:  # pragma: Python 3
        import rapidjson as json
    except ImportError:  # pragma: Python 2
        _use_rapidjson = False


_json_encoder = None


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
    if backwards.PY2 or _use_rapidjson:  # pragma: Python 2
        # Character indents not allowed in Python 2 json
        indent = indent_char2int(indent)
    kwargs['indent'] = indent
    kwargs['sort_keys'] = sort_keys
    if fd is None:
        return backwards.as_bytes(json.dumps(obj, **kwargs))
    else:
        if backwards.PY2:  # pragma: Python 2
            kwargs.setdefault('indent', 4)
        else:  # pragma: Python 3
            kwargs.setdefault('indent', '\t')
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
        return json.loads(backwards.as_str(msg), **kwargs)
    else:
        # For files
        return json.load(msg, **kwargs)
    

class JSONReadableEncoder(stdjson.JSONEncoder):
    r"""Encoder class for Ygg messages."""

    def default(self, o):  # pragma: no cover
        r"""Encoder that allows for expansion types."""
        from yggdrasil.metaschema.datatypes import get_registered_types
        for cls in get_registered_types().values():
            if (not cls._replaces_existing) and cls.validate(o):
                new_o = cls.encode_data_readable(o, None)
                return new_o
        return stdjson.JSONEncoder.default(self, o)


# class JSONEncoder(stdjson.JSONEncoder):
#     r"""Encoder class for Ygg messages."""

#     def default(self, o):
#         r"""Encoder that allows for expansion types."""
#         for cls in get_registered_types():
#             if cls.validate(o):
#                 new_o = cls.encode_data(o, None)
#                 return new_o
#         return stdjson.JSONEncoder.default(self, o)

    
# class JSONDecoder(stdjson.JSONDecoder):
#     r"""Decoder class for Ygg messages."""
#
#     def raw_decode(self, s, idx=0):
#         r"""Decoder that further decodes objects."""
