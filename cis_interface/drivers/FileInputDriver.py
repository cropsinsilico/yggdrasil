from cis_interface.drivers.ConnectionDriver import ConnectionDriver
from cis_interface.schema import register_component


@register_component
class FileInputDriver(ConnectionDriver):
    r"""Class that sends messages read from a file.

    Args:
        name (str): Name of the queue that messages should be sent to.
        args (str): Path to the file that messages should be read from.
        **kwargs: Additional keyword arguments are passed to the parent class.

    """

    _icomm_type = 'FileComm'
    _is_input = True

    def __init__(self, name, args, **kwargs):
        kwargs.setdefault('icomm_kws', {})
        kwargs['icomm_kws']['address'] = args
        super(FileInputDriver, self).__init__(name, **kwargs)
        self.debug('(%s)', args)
