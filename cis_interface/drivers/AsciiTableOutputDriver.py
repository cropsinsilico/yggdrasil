from cis_interface import serialize
from cis_interface.drivers.AsciiFileOutputDriver import AsciiFileOutputDriver
from cis_interface.schema import register_component


@register_component
class AsciiTableOutputDriver(AsciiFileOutputDriver):
    r"""Class to handle output of received messages to an ASCII table.

    Args:
        name (str): Name of the output queue to receive messages from.
        args (str or dict): Path to the file that messages should be written to
            or dictionary containing the filepath and other keyword arguments
            to be passed to the created AsciiTable object.
        format_str (str): Format string that should be used to format
            output in the case that the io_mode is 'w' (write). It is not
            required if the io_mode is any other value.
        field_names (list, optional): List of column names. Defaults to None.
        field_units (list, optional): List of column units. Defaults to None.
        use_astropy (bool, optional): If True, astropy is used to determine
            a table's format if it is installed. If False, a format string
            must be contained in the table. Defaults to False.
        delimiter (str, optional): String that should be used to separate
            columns. Default set by serialize._default_delimiter.
        comment (str, optional): String that should be used to identify
            comments. Default set by serialize._default_comment.
        newline (str, optional): String that should be used to identify
            the end of a line. Default set by serialize._default_newline.
        as_array (bool, optional): If True, the table contents are sent all at
            once as an array. Defaults to False.
        **kwargs: Additional keyword arguments are passed to parent class.

    """

    _ocomm_type = 'AsciiTableComm'

    def __init__(self, name, args, **kwargs):
        alias_keys = [('column_names', 'field_names'),
                      ('column_units', 'field_units'),
                      ('column', 'delimiter')]
        for old, new in alias_keys:
            if kwargs.get(old, None) is not None:
                kwargs.setdefault(new, kwargs.pop(old))
        super(AsciiTableOutputDriver, self).__init__(name, args, **kwargs)
        self.debug('(%s)', args)

    def update_serializer(self, msg):
        r"""Update the serializer for the output comm based on input."""
        sinfo = self.ocomm.serializer.serializer_info
        sinfo['stype'] = 3
        sinfo.setdefault('format_str', self.icomm.serializer.format_str)
        sinfo.setdefault('field_names', self.icomm.serializer.field_names)
        sinfo.setdefault('field_units', self.icomm.serializer.field_units)
        self.ocomm.serializer = serialize.get_serializer(**sinfo)
