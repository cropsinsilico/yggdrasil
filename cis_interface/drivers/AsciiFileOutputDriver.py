from cis_interface.drivers.FileOutputDriver import FileOutputDriver
from cis_interface.schema import register_component


@register_component
class AsciiFileOutputDriver(FileOutputDriver):
    r"""Class to handle output line by line to an ASCII file.

    Args:
        name (str): Name of the output queue to receive messages from.
        args (str or dict): Path to the file that messages should be written to
            or dictionary containing the filepath and other keyword arguments
            to be passed to the created AsciiFile object.
        comment (str, optional): String that should be used to identify
                comments. Default set by :class:`AsciiFile`.
        newline (str, optional): String that should be used to identify
                the end of a line. Default set by :class:`AsciiFile`.
        **kwargs: Additional keyword arguments are passed to parent class.

    """

    _ocomm_type = 'AsciiFileComm'
