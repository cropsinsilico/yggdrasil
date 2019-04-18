from yggdrasil.components import import_component
from yggdrasil.communication.CommBase import CommBase


class DefaultComm(CommBase):
    r"""Simple wrapper for default class that allows it to be registered."""

    _commtype = 'default'
    _schema_subtype_description = ('Communication mechanism selected '
                                   'based on the current platform.')

    def __new__(cls, *args, **kwargs):
        if kwargs.get('commtype', None) == cls._commtype:
            kwargs.pop('commtype')
        return cls._get_alias()(*args, **kwargs)

    @classmethod
    def _get_alias(cls):
        r"""Initialize the default comm class as the alias.

        Returns:
            class: The actual default comm class that this class represents.

        """
        if not hasattr(cls, '_alias'):
            from yggdrasil.tools import get_default_comm
            cls._alias = import_component('comm', get_default_comm())
        return cls._alias
