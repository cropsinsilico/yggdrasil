"""Module for sending output to a RabbitMQ server."""
from cis_interface.drivers.OutputDriver import OutputDriver
from cis_interface.schema import register_component


@register_component
class RMQOutputDriver(OutputDriver):
    r"""Driver for sending output to a RabbitMQ server.

    Args:
        name (str): The name of the local message queue that the driver should
            connect to.
        args (str): The name of the RabbitMQ message queue that the driver
            connect to.
        **kwargs: Additional keyword arguments are passed to parent class.

    """

    _ocomm_type = 'RMQComm'
    
    def __init__(self, name, args, **kwargs):
        kwargs.setdefault('ocomm_kws', {})
        kwargs['ocomm_kws']['queue'] = args
        super(RMQOutputDriver, self).__init__(name, args, **kwargs)
