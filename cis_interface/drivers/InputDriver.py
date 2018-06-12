from cis_interface.drivers.ConnectionDriver import ConnectionDriver
from cis_interface.schema import register_component


@register_component
class InputDriver(ConnectionDriver):
    r"""Driver for receiving input from another model's comm via a local comm.

    Args:
        name (str): The name of the local message comm that the driver should
            connect to.
        args (str): The name of the other message comm that the driver should
            connect to.
        **kwargs: Additional keyword arguments are passed to parent class.

    """

    _is_input = True

    def __init__(self, name, args, **kwargs):
        icomm_kws = kwargs.get('icomm_kws', {})
        icomm_kws['name'] = args
        icomm_kws['no_suffix'] = True
        kwargs['icomm_kws'] = icomm_kws
        super(InputDriver, self).__init__(name, **kwargs)
        self.comm_env.update(**self.icomm.opp_comms)
