from cis_interface.drivers.FileInputDriver import FileInputDriver
from cis_interface.schema import register_component


@register_component
class AsciiFileInputDriver(FileInputDriver):
    r"""Class that sends lines from an ASCII file.

    Args:
        name (str): Name of the queue that messages should be sent to.
        args (str or dict): Path to the file that messages should be read from
            or dictionary containing the filepath and other keyword arguments
            to be passed to the created AsciiFile object.
        comment (str, optional): String that should be used to identify
                comments. Default set by :class:`AsciiFile`.
        newline (str, optional): String that should be used to identify
                the end of a line. Default set by :class:`AsciiFile`.
        **kwargs: Additional keyword arguments are passed to parent class.

    """

    _icomm_type = 'AsciiFileComm'
