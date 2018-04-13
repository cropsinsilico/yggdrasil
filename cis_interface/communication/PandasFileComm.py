from cis_interface.communication.FileComm import FileComm


class PandasFileComm(FileComm):
    r"""Class for handling I/O from/to a pandas csv file on disk.

    Args:
        name (str): The environment variable where communication address is
            stored.
        delimiter (str, optional): String that should be used to separate
            columns. Defaults to '\t'.
        **kwargs: Additional keywords arguments are passed to parent class.

    """
    def _init_before_open(self, delimiter='\t', serializer_kwargs=None, **kwargs):
        r"""Set up dataio and attributes."""
        if serializer_kwargs is None:
            serializer_kwargs = {}
        serializer_kwargs.update(stype=6, delimiter=delimiter)
        kwargs['serializer_kwargs'] = serializer_kwargs
        super(PandasFileComm, self)._init_before_open(**kwargs)
        self.read_meth = 'read'
        if self.append:
            self.serializer.write_header = False
