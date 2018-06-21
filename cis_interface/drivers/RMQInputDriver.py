"""Module for receiving input from a RabbitMQ server."""
from cis_interface.drivers.InputDriver import InputDriver
from cis_interface.schema import register_component


@register_component
class RMQInputDriver(InputDriver):
    r"""Driver for receiving input from a RabbitMQ server via a local comm.

    Args:
        name (str): The name of the local message queue that the driver should
            connect to.
        args (str): The name of the RabbitMQ message queue that the driver
            should connect to.
        **kwargs: Additional keyword arguments are passed to parent class.

    """

    _icomm_type = 'RMQComm'

    def __init__(self, name, args, **kwargs):
        kwargs.setdefault('icomm_kws', {})
        kwargs['icomm_kws']['queue'] = args
        super(RMQInputDriver, self).__init__(name, args, **kwargs)
