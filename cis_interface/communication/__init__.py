import importlib
from cis_interface import platform


if platform._is_win:
    _default_comm = 'ZMQComm'
else:
    _default_comm = 'IPCComm'


def get_comm_class(comm=None):
    r"""Return a communication class given it's name.

    Args:
        comm (str, optional): Name of communicator class. Defaults to
            _default_comm if not provided.

    Returns:
        class: Communicator class.

    """
    if comm is None:
        comm = _default_comm
    mod = importlib.import_module('cis_interface.communication.%s' % comm)
    comm_cls = getattr(mod, comm)
    return comm_cls


def get_comm(name, comm=None, **kwargs):
    r"""Return communicator for existing comm components.

    Args:
        name (str): Communicator name.
        comm (str, optional): Name of communicator class.
        **kwargs: Additional keyword arguments are passed to communicator class.

    Returns:
        Comm: Communicator of given class.

    """
    if comm is None:
        comm = _default_comm
    comm_cls = get_comm_class(comm)
    return comm_cls(name, **kwargs)
    

def new_comm(name, comm=None, **kwargs):
    r"""Return a new communicator, creating necessary components for
    communication (queues, sockets, channels, etc.).

    Args:
        name (str): Communicator name.
        comm (str, optional): Name of communicator class.
        **kwargs: Additional keyword arguments are passed to communicator
            class method new_comm.

    Returns:
        Comm: Communicator of given class.

    """
    if comm is None:
        comm = _default_comm
    comm_cls = get_comm_class(comm)
    return comm_cls.new_comm(name, **kwargs)


DefaultComm = get_comm_class()


__all__ = ['new_comm', 'get_comm', 'get_comm_class']
