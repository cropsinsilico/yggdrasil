from cis_interface.drivers.AsciiFileInputDriver import AsciiFileInputDriver
from cis_interface.tools import eval_kwarg


class AsciiTableInputDriver(AsciiFileInputDriver):
    r"""Class to handle input from an ASCII table.

    Args:
        name (str): Name of the input queue to send messages to.
        args (str or dict): Path to the file that messages should be read from
            or dictionary containing the filepath and other keyword arguments
            to be passed to the created AsciiTable object.
        format_str (str): Format string that should be used to format
            output in the case that the io_mode is 'w' (write). It is not
            required if the io_mode is any other value.
        dtype (str): Numpy structured data type for each row. If not
            provided it is set using format_str. Defaults to None.
        column_names (list, optional): List of column names. Defaults to
            None.
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
        **kwargs: Additional keyword arguments are passed to parent class.

    """
    def __init__(self, name, args, **kwargs):
        file_keys = ['format_str', 'dtype', 'column_names', 'use_astropy',
                     'column', 'as_array']
        icomm_kws = kwargs.get('icomm_kws', {})
        icomm_kws.setdefault('comm', 'AsciiTableComm')
        for k in file_keys:
            if k in kwargs:
                icomm_kws[k] = kwargs.pop(k)
                # Eval commands non-string args from yaml string
                if k in ['column_names', 'use_astropy', 'as_array']:
                    icomm_kws[k] = eval_kwarg(icomm_kws[k])
        kwargs['icomm_kws'] = icomm_kws
        super(AsciiTableInputDriver, self).__init__(name, args, **kwargs)
        self.debug('(%s)', args)

    def before_loop(self):
        r"""Open the file and send the format string."""
        super(AsciiTableInputDriver, self).before_loop()
        self.send_message(self.icomm.file.format_str)

    def send_message(self, msg):
        r"""Send a single message as no limit message.

        Args:
            msg (str): Message to be sent.

        Returns:
            bool: Success or failure of send.

        """
        return super(AsciiTableInputDriver, self).send_message(msg, nolimit=True)
