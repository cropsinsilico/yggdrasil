from cis_interface.drivers.FileOutputDriver import FileOutputDriver


class PickleFileOutputDriver(FileOutputDriver):
    r"""Class that writes received messages to a file.

    Args:
        name (str): Name of the queue that messages should be sent to.
        args (str): Path to the file that messages should be read from.
        **kwargs: Additional keyword arguments are passed to the parent class.

    """
    def __init__(self, name, args, **kwargs):
        # icomm_kws = kwargs.get('icomm_kws', {})
        ocomm_kws = kwargs.get('ocomm_kws', {})
        ocomm_kws.setdefault('comm', 'PickleFileComm')
        kwargs['ocomm_kws'] = ocomm_kws
        super(PickleFileOutputDriver, self).__init__(name, args, **kwargs)
        self.debug('(%s)', args)

    def recv_message(self, **kwargs):
        r"""Get a new message to send.

        Returns:
            str, bool: False if no more messages, message otherwise.

        """
        return super(PickleFileOutputDriver, self).recv_message(
            nolimit=True, **kwargs)
