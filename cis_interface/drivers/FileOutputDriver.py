from cis_interface.drivers.ConnectionDriver import ConnectionDriver
from cis_interface.schema import register_component


@register_component
class FileOutputDriver(ConnectionDriver):
    r"""Class to handle output of received messages to a file.

    Args:
        name (str): Name of the output queue to receive messages from.
        path (str): Path to the file that messages should be written to.
        in_temp (bool, str, optional): If True or 'True', the path will be
            considered relative to the temporary directory. Defaults to False.
        **kwargs: Additional keyword arguments are passed to the parent class.

    """

    _ocomm_type = 'FileComm'
    _is_output = True

    def __init__(self, name, path, in_temp=False, **kwargs):
        if isinstance(in_temp, str):
            in_temp = eval(in_temp)
        ocomm_kws = kwargs.get('ocomm_kws', {})
        ocomm_kws['address'] = path
        ocomm_kws['in_temp'] = in_temp
        kwargs['ocomm_kws'] = ocomm_kws
        super(FileOutputDriver, self).__init__(name, **kwargs)
        self.env[self.name] = self.icomm.address
        self.debug('(%s)', path)
