from cis_interface import serialize
from cis_interface.drivers.FileInputDriver import FileInputDriver
from cis_interface.schema import register_component


@register_component
class PandasFileInputDriver(FileInputDriver):
    r"""Class to handle input from a Pandas csv file.

    Args:
        name (str): Name of the input queue to send messages to.
        args (str or dict): Path to the file that messages should be read from.
        delimiter (str, optional): String that should be used to separate
            columns. Defaults to '\t'.
        **kwargs: Additional keyword arguments are passed to parent class.

    """

    _icomm_type = 'PandasFileComm'

    def __init__(self, name, args, **kwargs):
        kwargs.setdefault('icomm_kws', {})
        kwargs['icomm_kws'].setdefault('recv_converter', serialize.pandas2numpy)
        super(PandasFileInputDriver, self).__init__(name, args, **kwargs)
        self.debug('(%s)', args)

    def update_serializer(self, msg):
        r"""Update the serializer for the output comm based on input."""
        pass
