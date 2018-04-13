from cis_interface import serialize
from cis_interface.drivers.FileOutputDriver import FileOutputDriver


class PandasFileOutputDriver(FileOutputDriver):
    r"""Class to handle output of received messages to a Pandas csv file.

    Args:
        name (str): Name of the output queue to receive messages from.
        args (str or dict): Path to the file that messages should be written to.
        delimiter (str, optional): String that should be used to separate
            columns. Defaults to '\t'.
        **kwargs: Additional keyword arguments are passed to parent class.

    """
    def __init__(self, name, args, **kwargs):
        file_keys = ['delimiter']
        # icomm_kws = kwargs.get('icomm_kws', {})
        ocomm_kws = kwargs.get('ocomm_kws', {})
        ocomm_kws.setdefault('comm', 'PandasFileComm')
        ocomm_kws.setdefault('send_converter', serialize.numpy2pandas)
        for k in file_keys:
            if k in kwargs:
                ocomm_kws[k] = kwargs.pop(k)
        kwargs['ocomm_kws'] = ocomm_kws
        super(PandasFileOutputDriver, self).__init__(name, args, **kwargs)
        self.debug('(%s)', args)

    def update_serializer(self, msg):
        r"""Update the serializer for the output comm based on input."""
        sinfo = self.ocomm.serializer.serializer_info
        sinfo['stype'] = 6  # Output as pandas csv
        sinfo.setdefault('format_str', self.icomm.serializer.format_str)
        sinfo.setdefault('field_names', self.icomm.serializer.field_names)
        sinfo.setdefault('field_units', self.icomm.serializer.field_units)
        self.ocomm.serializer = serialize.get_serializer(**sinfo)
