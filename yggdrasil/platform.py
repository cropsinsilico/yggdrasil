r"""This module handle platform compatibility issues."""
import sys
import numpy as np
from platform import machine


_is_64bit = (sys.maxsize > 2**32)
_is_mac = (sys.platform == 'darwin')
_is_linux = ('linux' in sys.platform)
_is_win = (sys.platform in ['win32', 'cygwin'])
_supported_platforms = ['Windows', 'MacOS', 'Linux']
_numpy2 = (np.lib.NumpyVersion(np.__version__) >= '2.0.0b1')
_machine = machine

if _is_win:  # pragma: windows
    _newline = b'\r\n'
    _platform = 'Windows'
else:
    _newline = b'\n'
    if _is_mac:
        _platform = 'MacOS'
    elif _is_linux:
        _platform = 'Linux'
_newline_str = _newline.decode("utf-8")
