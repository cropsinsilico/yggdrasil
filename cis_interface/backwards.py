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
    np_dtype_str = 'U'


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
        b = unicode2bytes(s)
        o = b.decode('unicode_escape')
    return o


def array_unicode2bytes(arr):
    r"""In Python 3, 'S' refers to raw bytes and any bytes written to a file
    will be prepended with a 'b' that will not be read in correctly with the
    %s format specifier. To get around this, this function converts parts of
    an array from 'U' to 'S' format so the array can be read as bytes."""
    if PY2:  # pragma: Python 2
        out = arr
    else:  # pragma: Python 3
        dtype = arr.dtype
        if len(dtype) == 0:
            new_dtype = np.dtype(str(arr.dtype).replace('U', 'S'))
        else:
            typs = []
            for i in range(len(dtype)):
                n = dtype.names[i]
                t = str(dtype[i])
                typs.append((n, np.dtype(t.replace('U', 'S'))))
            new_dtype = np.dtype(typs)
        out = arr.astype(new_dtype)
    return out


def array_bytes2unicode(arr):
    r"""In Python 3, 'S' refers to raw bytes and any bytes written to a file
    will be prepended with a 'b' that will not be read in correctly with the
    %s format specifier. To get around this, this function converts parts of
    an array from 'S' to 'U' format so the array can be written."""
    if PY2:  # pragma: Python 2
        out = arr
    else:  # pragma: Python 3
        dtype = arr.dtype
        if len(dtype) == 0:
            new_dtype = np.dtype(str(arr.dtype).replace('S', 'U'))
        else:
            typs = []
            for i in range(len(dtype)):
                n = dtype.names[i]
                t = str(dtype[i])
                typs.append((n, np.dtype(t.replace('S', 'U'))))
            new_dtype = np.dtype(typs)
        out = arr.astype(new_dtype)
    return out


# https://github.com/numpy/numpy/issues/3184
genfromtxt_old = np.genfromtxt


@functools.wraps(genfromtxt_old)
def genfromtxt_py3_fixed(f, encoding="utf-8", *args, **kwargs):
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


if sys.version_info >= (3,):
    np.genfromtxt = genfromtxt_py3_fixed

    
__all__ = ['pickle', 'configparser', 'sio',
           'decode_str', 'bytes2unicode', 'unicode2bytes']
