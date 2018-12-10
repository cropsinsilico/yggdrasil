from cis_interface.drivers.FileOutputDriver import FileOutputDriver
from cis_interface.schema import register_component


@register_component
class PandasFileOutputDriver(FileOutputDriver):
    r"""Class to handle output of received messages to a Pandas csv file.

    Args:
        name (str): Name of the output queue to receive messages from.
        args (str or dict): Path to the file that messages should be written to.
        delimiter (str, optional): String that should be used to separate
            columns. Defaults to '\t'.
        **kwargs: Additional keyword arguments are passed to parent class.

    """

    _ocomm_type = 'PandasFileComm'
