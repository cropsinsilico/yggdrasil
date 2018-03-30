import importlib
from cis_interface import tools


def get_comm_class(comm=None):
    r"""Return a communication class given it's name.

    Args:
        comm (str, optional): Name of communicator class. Defaults to
            tools.get_default_comm() if not provided.

    Returns:
        class: Communicator class.

    """
    if comm is None:
        comm = tools.get_default_comm()
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
        comm = tools.get_default_comm()
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
        comm = tools.get_default_comm()
    # elif comm == 'ErrorComm':
    #     comm = kwargs.get('base_comm', tools.get_default_comm())
    #     kwargs['new_comm_class'] = 'ErrorComm'
    comm_cls = get_comm_class(comm)
    return comm_cls.new_comm(name, **kwargs)


def DefaultComm(*args, **kwargs):
    r"""Construct a comm object of the default type."""
    return get_comm_class()(*args, **kwargs)


def cleanup_comms(comm=None):
    r"""Call cleanup_comms for the appropriate communicator class.

    Args:
        comm (str, optional): Name of communicator class. Defaults to
            tools.get_default_comm() if not provided.

    Returns:
        int: Number of comms closed.

    """
    return get_comm_class(comm).cleanup_comms()


__all__ = ['new_comm', 'get_comm', 'get_comm_class', 'cleanup_comms',
           'DefaultComm']
