from cis_interface.drivers.FileOutputDriver import FileOutputDriver


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
    
    def __init__(self, name, args, **kwargs):
        file_keys = ['comment', 'newline']
        # icomm_kws = kwargs.get('icomm_kws', {})
        ocomm_kws = kwargs.get('ocomm_kws', {})
        ocomm_kws.setdefault('comm', 'AsciiFileComm')
        for k in file_keys:
            if k in kwargs:
                ocomm_kws[k] = kwargs.pop(k)
        kwargs['ocomm_kws'] = ocomm_kws
        super(AsciiFileOutputDriver, self).__init__(name, args, **kwargs)
        self.debug('(%s)', args)
