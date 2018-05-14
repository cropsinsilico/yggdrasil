from cis_interface.drivers.FileInputDriver import FileInputDriver


class AsciiMapInputDriver(FileInputDriver):
    r"""Class that sends messages read from a ASCII map file.

    Args:
        name (str): Name of the queue that messages should be sent to.
        args (str): Path to the file that messages should be read from.
        **kwargs: Additional keyword arguments are passed to the parent class.

    """
    def __init__(self, name, args, **kwargs):
        icomm_kws = kwargs.get('icomm_kws', {})
        # ocomm_kws = kwargs.get('ocomm_kws', {})
        icomm_kws.setdefault('comm', 'AsciiMapComm')
        kwargs['icomm_kws'] = icomm_kws
        super(AsciiMapInputDriver, self).__init__(name, args, **kwargs)
        self.debug('(%s)', args)
