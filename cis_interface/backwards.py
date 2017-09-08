r"""This module allows for backward compatibility."""
import sys
PY2 = (sys.version_info[0] == 2)
if PY2:  # pragma: Python 2
    import cPickle as pickle
    import ConfigParser as configparser
    import StringIO as sio
else:  # pragma: Python 3
    import pickle
    import configparser
    import io as sio


def bytes2str(b):
    r"""Convert from bytes/bytearray/str to string.

    Arguments:
        b (bytes, bytearray, str): Bytes to be converted into a string.

    Returns:
        str: String version of bytes/bytearray/str object.

    Raises:
       TypeError: If supplied type cannot be converted to string.

    """
    if PY2:  # pragma: Python 2
        if isinstance(b, (str, bytearray)):
            s = str(b)
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


def str2bytes(s):
    r"""Convert from a string to a bytes/bytearray object.

    Arguments:
        s (str, bytes, bytearray): Object to convert to a bytes version.

    Returns:
        bytes/bytearray: Bytes version of input.

    Raises:
       TypeError: If supplied type cannot be converted to bytes.

    """
    if PY2:  # pragma: Python 2
        if isinstance(s, bytearray):
            b = s
        elif isinstance(s, str):
            b = bytearray(s)
        else:
            raise TypeError("Cannot convert type %s to bytearray" % type(s))
    else:  # pragma: Python 3
        if isinstance(s, (bytes, bytearray)):
            b = s
        elif isinstance(s, str):
            b = s.encode('utf-8')
        else:
            raise TypeError("Cannot convert type %s to bytes" % type(s))
    return b


def decode_str(s):
    r"""Decode string escapes from a stirng.

    Arguments:
        s (str): String that escape sequences should be decoded from.

    Returns:
        str: Resulting string with escape sequences decoded.

    """
    if PY2:  # pragma: Python 2
        o = s.decode('string_escape')
    else:  # pragma: Python 3
        b = str2bytes(s)
        o = b.decode('unicode_escape')
    return o

    
__all__ = ['pickle', 'configparser', 'sio', 'decode_str']
