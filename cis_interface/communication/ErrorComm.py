from cis_interface.tests import ErrorClass
from cis_interface.communication import get_comm_class


def ErrorComm(name, base_comm='CommBase', **kwargs):
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
    base_class = get_comm_class(base_comm)
    out = ErrorClass(base_class, name, **kwargs)
    if base_comm is None:
        base_comm = str(base_class).split("'")[1].split(".")[-1]
    out._comm_class = base_comm
    return out
