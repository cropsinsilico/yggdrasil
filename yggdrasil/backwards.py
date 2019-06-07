r"""This module allows for backward compatibility."""
import sys
import time
import base64
from collections import OrderedDict
from yggdrasil.scanf import scanf
_python_version = '%d.%d' % (sys.version_info[0], sys.version_info[1])
PY2 = (sys.version_info[0] == 2)
PY34 = ((sys.version_info[0] == 3) and (sys.version_info[1] == 4))
if PY2:  # pragma: Python 2
    import cPickle as pickle
    import ConfigParser as configparser
    import StringIO as sio
    from __builtin__ import unicode
    import types
    BytesIO = sio.StringIO
    StringIO = sio.StringIO
    file_type = types.FileType
    bytes_type = str
    unicode_type = unicode
    string_type = str
    np_dtype_str = 'S'
    string_types = (str, unicode, bytearray)
    class_types = (type, types.ClassType)
    base64_encode = base64.encodestring
    base64_decode = base64.decodestring
else:  # pragma: Python 3
    import pickle
    import configparser
    import io as sio
    BytesIO = sio.BytesIO
    StringIO = sio.StringIO
    file_type = sio.IOBase
    bytes_type = bytes
    unicode_type = str
    string_type = str
    unicode = None
    np_dtype_str = 'S'
    string_types = (bytes, str, bytearray)
    class_types = (type, )
    base64_encode = base64.encodebytes
    base64_decode = base64.decodebytes
if sys.version_info >= (3, 3):
    clock_time = time.perf_counter
else:
    clock_time = time.clock


def scanf_bytes(fmt, bytes_line):
    r"""Extract parameters from a bytes object using scanf."""
    if PY2:  # pragma: Python 2
        out_byt = scanf(fmt, bytes_line)
    else:  # pragma: Python 3
        out_str = scanf(as_str(fmt), as_str(bytes_line))
        out_byt = match_stype(bytes_line, out_str, recurse=True,
                              allow_pass=True)
    return out_byt


def assert_str(s):
    r"""Assert that the input is in str type appropriate for the version of
    Python.

    Arguments:
        s (obj): Object to be tested if it is of the proper str class.

    Raises:
        AssertionError: If the object is not in the proper str class.

    """
    assert(isinstance(s, string_type))


def assert_bytes(s):
    r"""Assert that the input is in bytes appropriate for the version of
    Python.

    Arguments:
        s (obj): Object to be tested if it is of the proper bytes class.

    Raises:
        AssertionError: If the object is not in the proper bytes class.

    """
    assert(isinstance(s, bytes_type))


def assert_unicode(s):
    r"""Assert that the input is in unicode appropriate for the version of
    Python.

    Arguments:
        s (obj): Object to be tested if it is of the proper unicode class.

    Raises:
        AssertionError: If the object is not in the proper unicode class.

    """
    assert(isinstance(s, unicode_type))


def recurse_conv(s, func_conv, **kwargs):
    r"""Recurse into list, tuples, or dicts, applying a conversion funciton.

    Args:
        s (object): Object to apply conversion to.
        func_conv (function): Callable conversion function that takes the object
            as input and returns a converted version of it.
        **kwargs: Additional keyword arguments are passed to the conversion
            function.

    Returns:
        object: Converted version of the object.

    Raises:
        TypeError: If the object is not a list, tuple, or dictionary.

    """
    if isinstance(s, list):
        s_out = []
        for i in range(len(s)):
            s_out.append(func_conv(s[i], **kwargs))
    elif isinstance(s, tuple):
        s_out = tuple(func_conv(list(s), **kwargs))
    elif isinstance(s, (dict, OrderedDict)):
        s_out = {}
        for k0 in s.keys():
            k = func_conv(k0, **kwargs)
            s_out[k] = func_conv(s[k0], **kwargs)
    else:
        raise TypeError("Cannot recurse into type: %s" % type(s))
    return s_out


def as_unicode(s_in, recurse=False, convert_types=None, allow_pass=False):
    r"""Convert from bytes/unicode/str to unicode.

    Arguments:
        s_in (bytes, unicode, str): Object to be converted into unicode.
        recurse (bool, optional): If True, objects that are lists, tuples, or
            dicts will be recursed into, converting string elements into
            unicode.
        convert_types (list, optional): Python types that should be converted
            to unicode. Defaults to the string types for the current Python
            version ([str, unicode, bytearray] in Python 2, [bytes, str,
            bytearray] otherwise).
        allow_pass (bool, optional): If True and the provided object is not
            converted, no error will be raised. Defaults to False and objects
            that cannot be converted will raise an error.

    Returns:
        unicode/str: Unicode version of input (unicode in Python 2, str in
            Python 3).

    Raises:
       TypeError: If supplied type cannot be converted to unicode and allow_pass
           is False.

    """
    if convert_types is None:
        convert_types = string_types
    if isinstance(s_in, convert_types):
        if PY2:  # pragma: Python 2
            if isinstance(s_in, (str, bytearray)):
                s_out = unicode_type(s_in)
            elif isinstance(s_in, unicode):
                s_out = s_in
            else:
                s_out = unicode_type(s_in)
        else:  # pragma: Python 3
            if isinstance(s_in, str):
                s_out = s_in
            elif isinstance(s_in, (bytes, bytearray)):
                s_out = s_in.decode("utf-8")
            else:
                s_out = unicode_type(s_in)
    elif recurse and isinstance(s_in, (list, tuple, dict, OrderedDict)):
        s_out = recurse_conv(s_in, as_unicode, recurse=True,
                             convert_types=convert_types, allow_pass=allow_pass)
    elif allow_pass:
        s_out = s_in
    else:
        raise TypeError("Cannot convert type %s to unicode." % type(s_in)
                        + "Must be one of: %s" % str(convert_types))
    return s_out


def as_bytes(s_in, recurse=False, convert_types=None, allow_pass=False):
    r"""Convert from bytes/unicode/str to a bytes object.

    Arguments:
        s_in (str, bytes, unicode): Object to convert to a bytes version.
        recurse (bool, optional): If True, objects that are lists, tuples, or
            dicts will be recursed into, converting string elements into
            unicode.
        convert_types (list, optional): Python types that should be converted
            to unicode. Defaults to the string types for the current Python
            version ([str, unicode, bytearray] in Python 2, [bytes, str,
            bytearray] otherwise).
        allow_pass (bool, optional): If True and the provided object is not
            converted, no error will be raised. Defaults to False and objects
            that cannot be converted will raise an error.

    Returns:
        bytes/str: Bytes version of input (str in Python 2, bytes in Python 3).

    Raises:
       TypeError: If supplied type cannot be converted to bytes.

    """
    if convert_types is None:
        convert_types = string_types
    if isinstance(s_in, convert_types):
        if PY2:  # pragma: Python 2
            if isinstance(s_in, bytearray):
                s_out = bytes_type(s_in)  # In python 2 str is bytes
            elif isinstance(s_in, str):
                s_out = s_in
            elif isinstance(s_in, unicode):
                s_out = s_in.encode("utf-8")
            else:
                s_out = str(s_in)
        else:  # pragma: Python 3
            if isinstance(s_in, bytes):
                s_out = s_in
            elif isinstance(s_in, bytearray):
                s_out = bytes_type(s_in)
            elif isinstance(s_in, str):
                s_out = s_in.encode("utf-8")
            else:
                s_out = as_bytes(str(s_in))
    elif recurse and isinstance(s_in, (list, tuple, dict, OrderedDict)):
        s_out = recurse_conv(s_in, as_bytes, recurse=True,
                             convert_types=convert_types, allow_pass=allow_pass)
    elif allow_pass:
        s_out = s_in
    else:
        raise TypeError("Cannot convert type %s to bytes." % type(s_in)
                        + "Must be one of: %s" % str(convert_types))
    return s_out
    

def as_str(s_in, recurse=False, convert_types=None, allow_pass=False):
    r"""Convert from bytes/unicode/str to a str object.

    Arguments:
        s_in (str, bytes, unicode): Object to convert to a str version.
        recurse (bool, optional): If True, objects that are lists, tuples, or
            dicts will be recursed into, converting string elements into
            unicode.
        convert_types (list, optional): Python types that should be converted
            to unicode. Defaults to the string types for the current Python
            version ([str, unicode, bytearray] in Python 2, [bytes, str,
            bytearray] otherwise).
        allow_pass (bool, optional): If True and the provided object is not
            converted, no error will be raised. Defaults to False and objects
            that cannot be converted will raise an error.

    Returns:
        str: Str version of input.

    Raises:
       TypeError: If supplied type cannot be converted to str.

    """
    if PY2:  # pragma: Python 2
        s_out = as_bytes(s_in, recurse=recurse, convert_types=convert_types,
                         allow_pass=allow_pass)
    else:  # pragma: Python 3
        s_out = as_unicode(s_in, recurse=recurse, convert_types=convert_types,
                           allow_pass=allow_pass)
    return s_out
    

def match_stype(s1, s2, **kwargs):
    r"""Encodes one string to match the type of the second.

    Args:
        s1 (str, bytes, bytearray, unicode): Object that type should be taken
            from.
        s2 (str, bytes, bytearray, unicode): Object that should be returned
            in the type from s1.
        **kwargs: Additional keyword arguments are passed to the conversion function.

    Returns:
        str, bytes, bytearray, unicode: Type matched version of s2.

    Raises:
        TypeError: If s1 is not str, bytes, bytearray or unicode.

    """
    if isinstance(s1, string_type):
        out = as_str(s2, **kwargs)
    elif isinstance(s1, bytes_type):
        out = as_bytes(s2, **kwargs)
    elif isinstance(s1, unicode_type):
        out = as_unicode(s2, **kwargs)
    elif isinstance(s1, bytearray):
        out = bytearray(as_unicode(s2), 'utf-8')
        if kwargs:  # pragma: debug
            raise RuntimeError("No conversion function for bytearray.")
    else:
        raise TypeError("Cannot match s1 type of '%s'" % type(s1))
    return out


def format_bytes(s, args):
    r"""Perform format on bytes/str, converting arguments to type of format
    string to ensure there is no prefix. For Python 3.4, if the format string
    is bytes, the formats and arguments will be changed to str type before
    format and then the resulting string will be changed back to bytes.

    Args:
        s (str, bytes): Format string.
        args (tuple): Arguments to be formated using the format string.

    Returns:
        str, bytes: Formatted argument string.

    """
    if PY2:  # pragma: Python 2
        out = s % args
    else:  # pragma: Python 3
        is_bytes = isinstance(s, bytes)
        new_args = []
        if PY34 or not is_bytes:
            converter = as_unicode
        else:
            converter = as_bytes
        for a in args:
            if isinstance(a, (bytes, str)):
                new_args.append(converter(a))
            else:
                new_args.append(a)
        out = converter(s) % tuple(new_args)
        if is_bytes:
            out = as_bytes(out)
    return out


def encode_escape(s):
    r"""Encode escape sequences.

    Args:
        s (str): String that should be encoded.

    Returns:
        str: Result of encoding escape sequences.

    """
    if PY2:  # pragma: Python 2
        out = match_stype(s, as_str(s).encode('string-escape'))
    else:  # pragma: Python 3
        out = match_stype(s, as_unicode(s).encode('unicode-escape'))
    return out


def decode_escape(s):
    r"""Decode escape sequences.

    Args:
        s (str): String that should be decoded.

    Returns:
        str: Result of decoding escape sequences.

    """
    if PY2:  # pragma: Python 2
        out = match_stype(s, as_bytes(s).decode('string-escape'))
    else:  # pragma: Python 3
        out = match_stype(s, as_bytes(s).decode('unicode-escape'))
    return out


# Python 3 version of np.genfromtxt
# https://github.com/numpy/numpy/issues/3184

    
__all__ = ['pickle', 'configparser', 'sio',
           'as_str', 'as_bytes', 'as_unicode']
