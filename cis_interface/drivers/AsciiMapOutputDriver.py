from cis_interface.drivers.FileOutputDriver import FileOutputDriver
from cis_interface.schema import register_component


@register_component
class AsciiMapOutputDriver(FileOutputDriver):
    r"""Class that writes received messages to a ASCII map file.

    Args:
        name (str): Name of the queue that messages should be sent to.
        args (str): Path to the file that messages should be read from.
        **kwargs: Additional keyword arguments are passed to the parent class.

    """

    _ocomm_type = 'AsciiMapComm'
