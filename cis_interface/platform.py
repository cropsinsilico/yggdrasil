r"""This module handle platform compatibility issues."""
import sys


_is_osx = (sys.platform == 'darwin')
_is_linux = ('linux' in sys.platform)
_is_win = (sys.platform in ['win32', 'cygwin'])

if _is_win:  # pragma: windows
    _newline = '\r\n'
    _platform = 'Windows'
else:
    _newline = '\n'
    if _is_osx:
        _platform = 'OSX'
    elif _is_linux:
        _platform = 'Linux'
