"""Module for receiving input from a RabbitMQ server."""
from cis_interface.drivers.InputDriver import InputDriver


class RMQInputDriver(InputDriver):
    r"""Driver for receiving input from a RabbitMQ server via a local comm.

    Args:
        name (str): The name of the local message queue that the driver should
            connect to.
        args (str): The name of the RabbitMQ message queue that the driver
            should connect to.
        **kwargs: Additional keyword arguments are passed to parent class.

    """

    def __init__(self, name, args, **kwargs):
        icomm_kws = kwargs.get('icomm_kws', {})
        # ocomm_kws = kwargs.get('ocomm_kws', {})
        icomm_kws.setdefault('comm', 'RMQComm')
        icomm_kws['queue'] = args
        kwargs['icomm_kws'] = icomm_kws
        super(RMQInputDriver, self).__init__(name, args, **kwargs)
