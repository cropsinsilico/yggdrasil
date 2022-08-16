import json as stdjson
import importlib
from yggdrasil.serialize.SerializeBase import SerializeBase
from yggdrasil import tools
from yggdrasil import rapidjson as json
try:
    _json_encoder = json.Encoder
    _json_decoder = json.Decoder
except AttributeError:
    print('RAPIDJSON:', dir(json))
    print('RAPIDJSON FILE:', json.__file__)
    raise


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
    if (len(pkg_mod) == 2) and (not s.startswith('http')) and (' ' not in s):
        try:
            mod = importlib.import_module(pkg_mod[0])
            s = getattr(mod, pkg_mod[1])
        except (ImportError, AttributeError):  # pragma: debug
            pass
    return s


class JSONReadableEncoder(stdjson.JSONEncoder):
    r"""Encoder class for Ygg messages."""

    def default(self, o):  # pragma: no cover
        r"""Encoder that allows for expansion types."""
        from yggdrasil.metaschema import MetaschemaTypeError
        from yggdrasil.metaschema.datatypes import encode_data_readable
        try:
            return encode_data_readable(o)
        except MetaschemaTypeError:
            raise TypeError("Cannot encode %s" % o)


class JSONEncoder(_json_encoder):
    r"""Encoder class for Ygg messages."""

    def default(self, o):
        r"""Encoder that allows for expansion types."""
        from yggdrasil.metaschema import MetaschemaTypeError
        from yggdrasil.metaschema.datatypes import encode_data
        try:
            return encode_data(o)
        except MetaschemaTypeError:
            raise TypeError("Cannot encode %s" % o)
    

class JSONDecoder(_json_decoder):
    r"""Decoder class for Ygg messages."""

    def string(self, s):
        r"""Try to parse string with class."""
        # TODO: Do this dynamically for classes based on an attribute
        return string2import(s)

    
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
    # Character indents not allowed in Python 2 json
    indent = indent_char2int(indent)
    kwargs['indent'] = indent
    kwargs['sort_keys'] = sort_keys
    if 'cls' in kwargs:
        kwargs.setdefault('default', kwargs.pop('cls')().default)
    else:
        kwargs.setdefault('default', JSONEncoder().default)
    if fd is None:
        return tools.str2bytes(json.dumps(obj, **kwargs))
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
    if isinstance(msg, (str, bytes)):
        msg_decode = tools.bytes2str(msg)
        func_decode = json.loads
    else:
        msg_decode = msg
        func_decode = json.load
    func_decode = JSONDecoder()
    return func_decode(msg_decode, **kwargs)


class JSONSerialize(SerializeBase):
    r"""Class for serializing a python object into a bytes message using JSON.

    Args:
        indent (str, int, optional): String or number of spaces that should be
            used to indent each level within the seiralized structure. Defaults
            to '\t'.
        sort_keys (bool, optional): If True, the serialization of dictionaries
            will be in key sorted order. Defaults to True.

    """

    _seritype = 'json'
    _schema_subtype_description = ('Serializes Python objects using the JSON '
                                   'standard.')
    _schema_properties = {
        'indent': {'type': ['string', 'int'], 'default': '\t'},
        'sort_keys': {'type': 'boolean', 'default': True}}
    default_datatype = {'type': 'object'}
    concats_as_str = False

    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args (obj): Python object to be serialized.

        Returns:
            bytes, str: Serialized message.

        """
        return encode_json(args, indent=self.indent, cls=JSONReadableEncoder)

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.

        Returns:
            obj: Deserialized Python object.

        """
        return decode_json(msg)

    @classmethod
    def concatenate(cls, objects, **kwargs):
        r"""Concatenate objects to get object that would be recieved if
        the concatenated serialization were deserialized.

        Args:
            objects (list): Objects to be concatenated.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            list: Set of objects that results from concatenating those provided.

        """
        if all([isinstance(x, dict) for x in objects]):
            total = dict()
            for x in objects:
                total.update(x)
            out = [total]
        elif all([isinstance(x, list) for x in objects]):
            total = list()
            for x in objects:
                total += x
            out = [total]
        else:
            # Adding additional list then causes set of objects to be serialized
            # as a JSON array
            out = [objects]
        return out
        
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
        out['contents'] = (b'{\n\t"a": [\n\t\t"b",\n\t\t1,\n\t\t1.0\n\t],'
                           b'\n\t"c": {\n\t\t"z": "hello"\n\t},'
                           b'\n\t"d": "new field"\n}')
        out['concatenate'] = [([{'a': 1}, {'b': 2}], [{'a': 1, 'b': 2}]),
                              ([['a'], ['b']], [['a', 'b']]),
                              ([['a'], {'b': 2}], [[['a'], {'b': 2}]])]
        # Version that allows for list concatentation
        # out['contents'] = (b'[\n\t'
        #                    b'{\n\t\t"a": [\n\t\t\t"b",\n\t\t\t1,\n\t\t\t1.0\n\t\t],'
        #                    b'\n\t\t"c": {\n\t\t\t"z": "hello"\n\t\t},'
        #                    b'\n\t\t"d": "new field"\n\t},'
        #                    b'\n\t2,\n\t2.0\n]')
        tab_rep = indent_char2int('\t') * b' '
        out['contents'] = out['contents'].replace(b'\t', tab_rep)
        return out
