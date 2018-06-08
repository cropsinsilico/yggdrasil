from cis_interface.drivers.FileInputDriver import FileInputDriver
from cis_interface.schema import register_component


@register_component
class PickleFileInputDriver(FileInputDriver):
    r"""Class that sends messages read from a file.

    Args:
        name (str): Name of the queue that messages should be sent to.
        args (str): Path to the file that messages should be read from.
        **kwargs: Additional keyword arguments are passed to the parent class.

    """

    _icomm_type = 'PickleFileComm'
