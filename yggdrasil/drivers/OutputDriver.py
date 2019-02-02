from yggdrasil.drivers.ConnectionDriver import ConnectionDriver
from yggdrasil.schema import register_component


@register_component
class OutputDriver(ConnectionDriver):
    r"""Driver for sending output to another model's comm via a local comm.

    Args:
        name (str): The name of the local message comm that the driver should
            connect to.
        args (str): The name of the other message comme that the driver should
            connect to.
        **kwargs: Additional keyword arguments are passed to parent class.

    """

    _connection_type = 'output'
    _direction = 'output'

    def __init__(self, name, args, **kwargs):
        kwargs.setdefault('ocomm_kws', {})
        kwargs['ocomm_kws']['name'] = args
        if kwargs['ocomm_kws'].get('comm', self._ocomm_type) == 'RMQComm':
            kwargs['ocomm_kws']['queue'] = args
        super(OutputDriver, self).__init__(name, **kwargs)
