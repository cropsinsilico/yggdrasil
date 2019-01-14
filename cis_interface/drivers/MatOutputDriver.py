from cis_interface.drivers.FileOutputDriver import FileOutputDriver
from cis_interface.serialize import MatSerialize, PickleSerialize


class MatOutputDriver(FileOutputDriver):
    r"""Class to handle output to .mat Matlab files.

    Args:
        name (str): Name of the output queue to receive messages from.
        args (str): Path to the file that messages should be written to.
        **kwargs: Additional keyword arguments are passed to parent class.

    """

    _ocomm_type = 'MatFileComm'
