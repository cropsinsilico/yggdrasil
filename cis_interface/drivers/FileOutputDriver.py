from cis_interface.drivers.ConnectionDriver import ConnectionDriver
from cis_interface.schema import register_component


@register_component
class FileOutputDriver(ConnectionDriver):
    r"""Class to handle output of received messages to a file.

    Args:
        name (str): Name of the output queue to receive messages from.
        args (str): Path to the file that messages should be written to.
        **kwargs: Additional keyword arguments are passed to the parent class.

    """

    _ocomm_type = 'FileComm'
    _is_output = True

    def __init__(self, name, args, **kwargs):
        kwargs.setdefault('ocomm_kws', {})
        kwargs['ocomm_kws']['address'] = args
        super(FileOutputDriver, self).__init__(name, **kwargs)
        self.env[self.name] = self.icomm.address
        self.debug('(%s)', args)
