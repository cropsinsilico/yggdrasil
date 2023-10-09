r"""This module handle platform compatibility issues."""
import sys


_is_64bit = (sys.maxsize > 2**32)
_is_mac = (sys.platform == 'darwin')
_is_linux = ('linux' in sys.platform)
_is_win = (sys.platform in ['win32', 'cygwin'])
_supported_platforms = ['Windows', 'MacOS', 'Linux']

if _is_win:  # pragma: windows
    _platform = 'Windows'
else:
    if _is_mac:
        _platform = 'MacOS'
    elif _is_linux:
        _platform = 'Linux'
