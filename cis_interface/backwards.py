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

    
def decode_str(s):
    r"""Decode string escapes from a stirng.

    Arguments:
        s (str): String that escape sequences should be decoded from.

    Returns:
        str: Resulting string with escape sequences decoded.

    """
    if PY2:  # pragma: Python 2
        o = s.decode('string_escape')
    else:
        if isinstance(s, str):
            b = s.encode('utf-8')
        else:
            b = s
        o = b.decode('unicode_escape')
    return o

    
__all__ = ['pickle', 'configparser', 'sio', 'decode_str']
