from cis_interface.drivers.FileInputDriver import FileInputDriver


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
    
    def __init__(self, name, args, **kwargs):
        file_keys = ['comment', 'newline']
        icomm_kws = kwargs.get('icomm_kws', {})
        # ocomm_kws = kwargs.get('ocomm_kws', {})
        icomm_kws.setdefault('comm', 'AsciiFileComm')
        for k in file_keys:
            if k in kwargs:
                icomm_kws[k] = kwargs.pop(k)
        kwargs['icomm_kws'] = icomm_kws
        super(AsciiFileInputDriver, self).__init__(name, args, **kwargs)
        self.debug('(%s)', args)
