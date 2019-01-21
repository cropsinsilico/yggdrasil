r"""This module handle platform compatibility issues."""
import sys


_is_mac = (sys.platform == 'darwin')
_is_linux = ('linux' in sys.platform)
_is_win = (sys.platform in ['win32', 'cygwin'])

if _is_win:  # pragma: windows
    _newline = b'\r\n'
    _platform = 'Windows'
else:
    _newline = b'\n'
    if _is_mac:
        _platform = 'MacOS'
    elif _is_linux:
        _platform = 'Linux'
