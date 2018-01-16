import importlib
from cis_interface.tools import _zmq_installed, _ipc_installed


if _zmq_installed:
    _default_comm = 'ZMQComm'
elif _ipc_installed:
    _default_comm = 'IPCComm'
else:  # pragma: debug
    raise Exception('Neither ZMQ or IPC installed.')


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


def get_comm(name, comm=None, new_comm_class=None, **kwargs):
    r"""Return communicator for existing comm components.

    Args:
        name (str): Communicator name.
        comm (str, optional): Name of communicator class.
        new_comm_class (str, optional): Name of communicator class that will
            override comm if set.
        **kwargs: Additional keyword arguments are passed to communicator class.

    Returns:
        Comm: Communicator of given class.

    """
    if comm is None:
        comm = _default_comm
    if new_comm_class is not None:
        comm = new_comm_class
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
    # elif comm == 'ErrorComm':
    #     comm = kwargs.get('base_comm', _default_comm)
    #     kwargs['new_comm_class'] = 'ErrorComm'
    comm_cls = get_comm_class(comm)
    return comm_cls.new_comm(name, **kwargs)


DefaultComm = get_comm_class()


__all__ = ['new_comm', 'get_comm', 'get_comm_class']
