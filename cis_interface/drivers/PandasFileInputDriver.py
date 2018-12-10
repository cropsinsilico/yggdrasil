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
