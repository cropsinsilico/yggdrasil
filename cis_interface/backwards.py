r"""This module allows for backward compatibility."""
import sys
import functools
import numpy as np
PY2 = (sys.version_info[0] == 2)
if PY2:  # pragma: Python 2
    import cPickle as pickle
    import ConfigParser as configparser
    import StringIO as sio
    from __builtin__ import unicode
    bytes_type = str
    unicode_type = str
    np_dtype_str = 'S'
else:  # pragma: Python 3
    import pickle
    import configparser
    import io as sio
    bytes_type = bytes
    unicode_type = str
    unicode = None
    np_dtype_str = 'S'


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
            s = bytes_type(b)
            # s = unicode(b)
        elif isinstance(b, unicode):
            s = bytes_type(b)
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
            b = bytes_type(s, 'utf-8')
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


# https://github.com/numpy/numpy/issues/3184
genfromtxt_old = np.genfromtxt


@functools.wraps(genfromtxt_old)
def genfromtxt_py3_fixed(f, encoding="utf-8", *args, **kwargs):  # pragma: Python 3
    if isinstance(f, sio.TextIOBase):
        if hasattr(f, "buffer") and hasattr(f.buffer, "raw") and \
           isinstance(f.buffer.raw, sio.FileIO):
            # Best case: get underlying FileIO stream (binary!) and use that
            fb = f.buffer.raw
            # Reset cursor on the underlying object to match that on wrapper
            fb.seek(f.tell())
            result = genfromtxt_old(fb, *args, **kwargs)
            # Reset cursor on wrapper to match that of the underlying object
            f.seek(fb.tell())
        else:
            # Not very good but works: Put entire contents into BytesIO object,
            # otherwise same ideas as above
            old_cursor_pos = f.tell()
            fb = sio.BytesIO(bytes(f.read(), encoding=encoding))
            result = genfromtxt_old(fb, *args, **kwargs)
            f.seek(old_cursor_pos + fb.tell())
    else:
        result = genfromtxt_old(f, *args, **kwargs)
    return result


if sys.version_info >= (3,):  # pragma: Python 3
    np.genfromtxt = genfromtxt_py3_fixed

    
__all__ = ['pickle', 'configparser', 'sio',
           'bytes2unicode', 'unicode2bytes']
