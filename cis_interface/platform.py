r"""This module handle platform compatibility issues."""
import sys


_is_osx = (sys.platform == 'darwin')
_is_linux = ('linux' in sys.platform)
_is_win = (sys.platform in ['win32', 'cygwin'])

if _is_win:  # pragma: windows
    _newline = '\r\n'
else:
    _newline = '\n'
