from yggdrasil.components import import_component
from yggdrasil.communication.CommBase import CommBase


class DefaultComm(CommBase):
    r"""Simple wrapper for default class that allows it to be registered."""

    _commtype = 'default'
    _schema_subtype_description = ('Communication mechanism selected '
                                   'based on the current platform.')

    def __new__(cls, *args, **kwargs):
        from yggdrasil.tools import get_default_comm
        print('here', args, kwargs)
        return import_component('comm', get_default_comm())(*args, **kwargs)
