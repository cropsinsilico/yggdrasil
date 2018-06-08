from cis_interface.drivers.FileOutputDriver import FileOutputDriver
from cis_interface.schema import register_component


@register_component
class PlyFileOutputDriver(FileOutputDriver):
    r"""Class that writes received messages to a file.

    Args:
        name (str): Name of the queue that messages should be sent to.
        args (str): Path to the file that messages should be read from.
        **kwargs: Additional keyword arguments are passed to the parent class.

    """

    _ocomm_type = 'PlyFileComm'

    def __init__(self, name, args, **kwargs):
        icomm_kws = kwargs.get('icomm_kws', {})
        icomm_kws.setdefault('serializer_type', 8)
        kwargs['icomm_kws'] = icomm_kws
        super(PlyFileOutputDriver, self).__init__(name, args, **kwargs)
        self.debug('(%s)', args)
