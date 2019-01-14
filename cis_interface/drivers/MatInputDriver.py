from cis_interface.drivers.FileInputDriver import FileInputDriver
from cis_interface.serialize import MatSerialize, PickleSerialize


class MatInputDriver(FileInputDriver):
    r"""Class that sends pickled dictionaries of matricies read from a .mat
    file.

    Args:
        name (str): Name of the queue that messages should be sent to.
        args (str): Path to the .mat file that messages should be read from.
        **kwargs: Additional keyword arguments are passed to parent class.

    """

    _icomm_type = 'MatFileComm'
