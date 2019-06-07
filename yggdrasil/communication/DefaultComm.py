from yggdrasil.components import import_component
from yggdrasil.communication.CommBase import CommBase


class DefaultComm(CommBase):
    r"""Simple wrapper for default class that allows it to be registered."""

    _commtype = 'default'
    _schema_subtype_description = ('Communication mechanism selected '
                                   'based on the current platform.')

    def __new__(cls, *args, **kwargs):
        return cls._get_alias()(*args, **kwargs)

    @classmethod
    def _reset_alias(cls):
        r"""Reset the alias so that it is recomputed the next time an instance
        is created."""
        cls._alias = None

    @classmethod
    def _get_alias(cls, overwrite=False):
        r"""Initialize the default comm class as the alias.

        Args:
            overwrite (bool, optional): If True, the existing aliased class will
                be replaced. Defaults to False

        Returns:
            class: The actual default comm class that this class represents.

        """
        if (getattr(cls, '_alias', None) is None) or overwrite:
            from yggdrasil.tools import get_default_comm
            cls._alias = import_component('comm', get_default_comm())
        return cls._alias
