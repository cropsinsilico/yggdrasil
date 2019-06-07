from yggdrasil.drivers.InputDriver import InputDriver


class FileInputDriver(InputDriver):
    r"""Class that sends messages read from a file.

    Args:
        name (str): Name of the queue that messages should be sent to.
        args (str): Path to the file that messages should be read from.
        **kwargs: Additional keyword arguments are passed to the parent class.

    """

    _connection_type = 'file_input'
    _icomm_type = 'FileComm'
    _schema_subtype_description = ('Connection between a file and a model.')

    def __init__(self, name, args, **kwargs):
        kwargs.setdefault('icomm_kws', {})
        kwargs['icomm_kws']['address'] = args
        super(FileInputDriver, self).__init__(name, args, **kwargs)
        self.debug('(%s)', args)
