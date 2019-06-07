from yggdrasil.drivers.OutputDriver import OutputDriver


class FileOutputDriver(OutputDriver):
    r"""Class to handle output of received messages to a file.

    Args:
        name (str): Name of the output queue to receive messages from.
        args (str): Path to the file that messages should be written to.
        **kwargs: Additional keyword arguments are passed to the parent class.

    """

    _connection_type = 'file_output'
    _ocomm_type = 'FileComm'
    _schema_subtype_description = ('Connection between a model and a file.')

    def __init__(self, name, args, **kwargs):
        kwargs.setdefault('ocomm_kws', {})
        kwargs['ocomm_kws']['address'] = args
        super(FileOutputDriver, self).__init__(name, args, **kwargs)
        self.debug('(%s)', args)
