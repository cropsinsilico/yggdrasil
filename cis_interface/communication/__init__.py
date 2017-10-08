import importlib


def new_comm(name, comm='IPCComm', **kwargs):
    r"""Return a new communicator.

    Args:
        name (str): Communicator name.
        comm (str, optional): Name of communicator class.
        **kwargs: Additional keyword arguments are passed to communicator class.

    Returns:
        Comm: Communicator of given class.

    """
    mod = importlib.import_module('cis_interface.communication.%s' % comm)
    comm_cls = getattr(mod, comm)
    return comm_cls.new_comm(name, **kwargs)


__all__ = ['new_comm']
