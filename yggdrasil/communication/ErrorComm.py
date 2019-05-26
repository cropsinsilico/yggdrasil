from yggdrasil.tests import ErrorClass
from yggdrasil.components import import_component


def ErrorComm(name, base_comm='CommBase', **kwargs):  # pragma: debug
    r"""Wrapper to return errored version of a comm class.

    Args:
        name (str): The environment variable where communication address is
            stored.
        base_comm (str, optional): Name of the base comm that should be used.
            Defaults to 'CommBase'.
        **kwargs: Additional keyword arguments are passed to the class
            constructor.

    Returns:
        ErrorClass: Instance of a comm class that will raise an error at the
            requested locaiton.

    """
    base_class = import_component('comm', base_comm)
    out = ErrorClass(base_class, name, **kwargs)
    return out
