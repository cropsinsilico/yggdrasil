"""Module for sending output to a RabbitMQ server."""
from cis_interface.drivers.OutputDriver import OutputDriver


class RMQOutputDriver(OutputDriver):
    r"""Driver for sending output to a RabbitMQ server.

    Args:
        name (str): The name of the local message queue that the driver should
            connect to.
        args (str): The name of the RabbitMQ message queue that the driver
            connect to.
        **kwargs: Additional keyword arguments are passed to parent class.

    """
    
    def __init__(self, name, args, **kwargs):
        # icomm_kws = kwargs.get('icomm_kws', {})
        ocomm_kws = kwargs.get('ocomm_kws', {})
        ocomm_kws.setdefault('comm', 'RMQComm')
        ocomm_kws['queue'] = args
        kwargs['ocomm_kws'] = ocomm_kws
        super(RMQOutputDriver, self).__init__(name, args, **kwargs)
