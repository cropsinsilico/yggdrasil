from cis_interface.drivers.ConnectionDriver import ConnectionDriver


class InputDriver(ConnectionDriver):
    r"""Driver for receiving input from another model's comm via a local comm.

    Args:
        name (str): The name of the local message comm that the driver should
            connect to.
        args (str): The name of the other message comme that the driver should
            connect to.
        **kwargs: Additional keyword arguments are passed to parent class.

    """

    def __init__(self, name, args, **kwargs):
        icomm_kws = kwargs.get('icomm_kws', {})
        # ocomm_kws = kwargs.get('ocomm_kws', {})
        icomm_kws['name'] = args
        icomm_kws['no_suffix'] = True
        kwargs['icomm_kws'] = icomm_kws
        super(InputDriver, self).__init__(name, **kwargs)
        self.comm_env[self.icomm.name] = self.icomm.address
