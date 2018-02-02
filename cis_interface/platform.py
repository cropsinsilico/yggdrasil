r"""This module handle platform compatibility issues."""
import sys
import os


_is_osx = (sys.platform == 'darwin')
_is_linux = ('linux' in sys.platform)
_is_win = (sys.platform in ['win32', 'cygwin'])

if _is_win:
    _newline = '\r\n'
    # This is required to fix crash on Windows in case of Ctrl+C
    # https://github.com/ContinuumIO/anaconda-issues/issues/905#issuecomment-232498034
    if _is_win:
        os.environ['FOR_DISABLE_CONSOLE_CTRL_HANDLER'] = '1'
else:
    _newline = '\n'
