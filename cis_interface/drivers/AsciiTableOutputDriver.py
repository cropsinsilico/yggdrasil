from cis_interface import serialize
from cis_interface.tools import eval_kwarg
from cis_interface.drivers.AsciiFileOutputDriver import AsciiFileOutputDriver


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
        dtype (str): Numpy structured data type for each row. If not
            provided it is set using format_str. Defaults to None.
        column_names (list, optional): List of column names. Defaults to None.
        column_units (list, optional): List of column units. Defaults to None.
        use_astropy (bool, optional): If True, astropy is used to determine
            a table's format if it is installed. If False, a format string
            must be contained in the table. Defaults to False.
        column (str, optional): String that should be used to separate
            columns. Default set by :class:`AsciiTable`.
        comment (str, optional): String that should be used to identify
            comments. Default set by :class:`AsciiFile`.
        newline (str, optional): String that should be used to identify
            the end of a line. Default set by :class:`AsciiFile`.
        as_array (bool, optional): If True, the table contents are sent all at
            once as an array. Defaults to False.
        timeout_recv_format (float, optional): Time in seconds that should be
            waited before giving up on recieving the format string. Defaults to
            60 s.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        timeout_recv_format (float): Time in seconds that should be waited
            before giving up on recieving the format string.

    """
    def __init__(self, name, args, timeout_recv_format=None, **kwargs):
        file_keys = ['format_str', 'dtype', 'column_names', 'column_units',
                     'use_astropy', 'column', 'as_array']
        # icomm_kws = kwargs.get('icomm_kws', {})
        ocomm_kws = kwargs.get('ocomm_kws', {})
        ocomm_kws.setdefault('comm', 'AsciiTableComm')
        for k in file_keys:
            if k in kwargs:
                ocomm_kws[k] = kwargs.pop(k)
                if k in ['column_names', 'column_units', 'use_astropy', 'as_array']:
                    ocomm_kws[k] = eval_kwarg(ocomm_kws[k])
        # ocomm_kws.setdefault('format_str', 'temp')
        kwargs['ocomm_kws'] = ocomm_kws
        super(AsciiTableOutputDriver, self).__init__(name, args, **kwargs)
        self.debug('(%s)', args)
        if timeout_recv_format is None:
            timeout_recv_format = 60
        self.timeout_recv_format = timeout_recv_format

    def update_serializer(self):
        r"""Update the serializer for the output comm based on input."""
        sinfo = self.ocomm.serializer.serializer_info
        sinfo['stype'] = 3
        sinfo.setdefault('format_str', self.icomm.serializer.format_str)
        sinfo.setdefault('field_names', self.icomm.serializer.field_names)
        sinfo.setdefault('field_units', self.icomm.serializer.field_units)
        self.ocomm.serializer = serialize.get_serializer(**sinfo)
