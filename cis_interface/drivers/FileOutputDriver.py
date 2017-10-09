from cis_interface.drivers.ConnectionDriver import ConnectionDriver


class FileOutputDriver(ConnectionDriver):
    r"""Class to handle output of received messages to a file.

    Args:
        name (str): Name of the output queue to receive messages from.
        args (str): Path to the file that messages should be written to.
        **kwargs: Additional keyword arguments are passed to the parent class.

    """
    def __init__(self, name, args, **kwargs):
        # icomm_kws = kwargs.get('icomm_kws', {})
        ocomm_kws = kwargs.get('ocomm_kws', {})
        ocomm_kws.setdefault('comm', 'FileComm')
        ocomm_kws['address'] = args
        kwargs['ocomm_kws'] = ocomm_kws
        super(FileOutputDriver, self).__init__(name, **kwargs)
        self.debug('(%s)', args)
