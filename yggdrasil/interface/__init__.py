r"""Routines for interfacing with framework from Python."""
# These import from the symbolic link for backwards compat
from yggdrasil.interface import YggInterface
from yggdrasil.interface.YggInterface import (
    YGG_MSG_EOF, YggInput, YggOutput)


__all__ = ['YggInterface', 'YggInput', 'YggOutput', 'YGG_MSG_EOF']
