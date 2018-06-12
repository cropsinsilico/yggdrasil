from cis_interface.drivers.ConnectionDriver import ConnectionDriver
from cis_interface.schema import register_component


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

    _is_output = True

    def __init__(self, name, args, **kwargs):
        ocomm_kws = kwargs.get('ocomm_kws', {})
        ocomm_kws['name'] = args
        ocomm_kws['no_suffix'] = True
        ocomm_kws['env'] = kwargs.get('comm_env', dict())
        kwargs['ocomm_kws'] = ocomm_kws
        super(OutputDriver, self).__init__(name, **kwargs)
