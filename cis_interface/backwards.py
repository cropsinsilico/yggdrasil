r"""This module allows for backward compatibility."""
import sys
import time
from cis_interface.scanf import scanf
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
    unicode_type = str
    string_type = str
    np_dtype_str = 'S'
    string_types = (str, unicode)
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
    string_types = (bytes, str)
if sys.version_info >= (3, 3):
    clock_time = time.perf_counter
else:
    clock_time = time.clock


def scanf_bytes(fmt, bytes_line):
    r"""Extract parameters from a bytes object using scanf."""
    if PY2:  # pragma: Python 2
        out_byt = scanf(fmt, bytes_line)
    else:  # pragma: Python 3
        out_uni = scanf(bytes2unicode(fmt), bytes2unicode(bytes_line))
        if isinstance(bytes_line, unicode_type):
            out_byt = out_uni
        else:
            if out_uni is None:
                out_byt = None
            else:
                out_byt = []
                for a in out_uni:
                    if isinstance(a, unicode_type):
                        out_byt.append(unicode2bytes(a))
                    else:
                        out_byt.append(a)
                out_byt = tuple(out_byt)
    return out_byt


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


def bytes2unicode(b):
    r"""Convert from bytes/unicode/str to unicode.

    Arguments:
        b (bytes, unicode, str): Bytes to be converted into unicode.

    Returns:
        unicode/str: String version of input.

    Raises:
       TypeError: If supplied type cannot be converted to unicode.

    """
    if PY2:  # pragma: Python 2
        if isinstance(b, (str, bytearray)):
            s = unicode_type(b)
            # s = unicode(b)
        elif isinstance(b, unicode):
            s = unicode_type(b)
            # s = b
        else:
            raise TypeError("Cannot convert type %s to str" % type(b))
    else:  # pragma: Python 3
        if isinstance(b, str):
            s = b
        elif isinstance(b, (bytes, bytearray)):
            s = b.decode("utf-8")
        else:
            raise TypeError("Cannot convert type %s to str" % type(b))
    return s


def unicode2bytes(s):
    r"""Convert from bytes/unicode/str to a bytes object.

    Arguments:
        s (str, bytes, unicode): Object to convert to a bytes version.

    Returns:
        bytes: Bytes version of input.

    Raises:
       TypeError: If supplied type cannot be converted to bytes.

    """
    if PY2:  # pragma: Python 2
        if isinstance(s, bytearray):
            b = bytes_type(s)  # In python 2 str is bytes
        elif isinstance(s, str):
            b = bytes_type(s)
        elif isinstance(s, unicode):
            b = s.encode("utf-8")
        else:
            raise TypeError("Cannot convert type %s to bytes" % type(s))
    else:  # pragma: Python 3
        if isinstance(s, bytes):
            b = bytes_type(s)
        elif isinstance(s, bytearray):
            b = bytes_type(s)
        elif isinstance(s, str):
            b = s.encode("utf-8")
            # b = bytes_type(s, 'utf-8')
            # b = bytearray(s.encode('utf-8'))
        else:
            raise TypeError("Cannot convert type %s to bytes" % type(s))
    return b


def match_stype(s1, s2):
    r"""Encodes one string to match the type of the second.

    Args:
        s1 (str, bytes, bytearray, unicode): Object that type should be taken
            from.
        s2 (str, bytes, bytearray, unicode): Object that should be returned
            in the type from s1.

    Returns:
        str, bytes, bytearray, unicode: Type matched version of s2.

    Raises:
        TypeError: If s1 is not str, bytes, bytearray or unicode.

    """
    if PY2:  # pragma: Python 2
        if isinstance(s1, str):
            out = unicode2bytes(s2)
        elif isinstance(s1, unicode):
            out = unicode(s2)
        elif isinstance(s1, bytearray):
            out = bytearray(bytes2unicode(s2), 'utf-8')
        else:
            raise TypeError("s1 must be str, bytes, bytearray or unicode.")
    else:  # pragma: Python 3
        if isinstance(s1, str):
            out = bytes2unicode(s2)
        elif isinstance(s1, bytes):
            out = unicode2bytes(s2)
        elif isinstance(s1, bytearray):
            out = bytearray(bytes2unicode(s2), 'utf-8')
        else:
            raise TypeError("s1 must be str, bytes, bytearray or unicode.")
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
            converter = bytes2unicode
        else:
            converter = unicode2bytes
        for a in args:
            if isinstance(a, (bytes, str)):
                new_args.append(converter(a))
            else:
                new_args.append(a)
        out = converter(s) % tuple(new_args)
        if is_bytes:
            out = unicode2bytes(out)
    return out


def encode_escape(s):
    r"""Encode escape sequences.

    Args:
        s (str): String that should be encoded.

    Returns:
        str: Result of encoding escape sequences.

    """
    if PY2:  # pragma: Python 2
        out = match_stype(s, bytes2unicode(s).encode('string-escape'))
    else:  # pragma: Python 3
        out = match_stype(s, bytes2unicode(s).encode('unicode-escape'))
    return out


def decode_escape(s):
    r"""Decode escape sequences.

    Args:
        s (str): String that should be decoded.

    Returns:
        str: Result of decoding escape sequences.

    """
    if PY2:  # pragma: Python 2
        out = match_stype(s, unicode2bytes(s).decode('string-escape'))
    else:  # pragma: Python 3
        out = match_stype(s, unicode2bytes(s).decode('unicode-escape'))
        # out = unicode2bytes(s).decode('unicode-escape').encode('latin1')
    return out


# Python 3 version of np.genfromtxt
# https://github.com/numpy/numpy/issues/3184

    
__all__ = ['pickle', 'configparser', 'sio',
           'bytes2unicode', 'unicode2bytes']
