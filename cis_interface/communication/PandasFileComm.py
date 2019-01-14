import numpy as np
from cis_interface import serialize
from cis_interface.communication.AsciiTableComm import AsciiTableComm
from cis_interface.schema import register_component
from cis_interface.serialize.PandasSerialize import PandasSerialize


def pandas_send_converter(obj):
    r"""Performs conversion from a limited set of objects to a Pandas data frame
    for sending to a file via PandasFileComm. Currently supports converting from
    structured numpy arrays, lists/tuples of numpy arrays, and dictionaries.

    Args:
        obj (object): Object to convert.

    Returns:
        pandas.DataFrame: Converted data frame (or unmodified input if conversion
            could not be completed.

    """
    if isinstance(obj, (list, tuple)):
        obj = serialize.list2pandas(obj)
    elif isinstance(obj, np.ndarray):
        obj = serialize.numpy2pandas(obj)
    elif isinstance(obj, dict):
        obj = serialize.dict2pandas(obj)
    return obj


def pandas_recv_converter(obj):
    r"""Performs conversion to a limited set of objects from a Pandas data frame
    for receiving from a file via PandasFileComm. Currently supports converting to
    lists/tuples of numpy arrays.

    Args:
        obj (pandas.DataFrame): Data frame to convert.

    Returns:
        list: pandas.DataFrame: Converted data frame (or unmodified input if conversion
            could not be completed.

    """
    return serialize.pandas2list(obj)


@register_component
class PandasFileComm(AsciiTableComm):
    r"""Class for handling I/O from/to a pandas csv file on disk.

    Args:
        name (str): The environment variable where communication address is
            stored.
        delimiter (str, optional): String that should be used to separate
            columns. Defaults to '\t'.
        **kwargs: Additional keywords arguments are passed to parent class.

    """

    _filetype = 'pandas'
    _default_serializer = PandasSerialize

    def _init_before_open(self, **kwargs):
        r"""Set up dataio and attributes."""
        kwargs.setdefault('send_converter', pandas_send_converter)
        kwargs.setdefault('recv_converter', pandas_recv_converter)
        super(PandasFileComm, self)._init_before_open(**kwargs)
        self.read_meth = 'read'
        if self.append:
            self.serializer.write_header = False

    @classmethod
    def get_testing_options(cls):
        r"""Method to return a dictionary of testing options for this class.

        Returns:
            dict: Dictionary of variables to use for testing. Key/value pairs:
                kwargs (dict): Keyword arguments for comms tested with the
                    provided content.
                send (list): List of objects to send to test file.
                recv (list): List of objects that will be received from a test
                    file that was sent the messages in 'send'.
                contents (bytes): Bytes contents of test file created by sending
                    the messages in 'send'.

        """
        out = super(PandasFileComm, cls).get_testing_options(as_array=True)
        order = out['recv'][0].dtype.names
        arr = out['send'][0]
        lst = [arr[n] for n in order]
        out['send'] = [lst, lst]
        out['recv'] = [[out['recv'][0][n] for n in order]]
        out['msg'] = out['send'][0]
        for k in ['format_str', 'as_array']:
            del out['kwargs'][k]
        out['contents'] = (b'name\tcount\tsize\n' +
                           b'one\t1\t1.0\n' +
                           b'two\t2\t2.0\n' +
                           b'three\t3\t3.0\n' +
                           b'one\t1\t1.0\n' +
                           b'two\t2\t2.0\n' +
                           b'three\t3\t3.0\n')
        return out
        
    def read_header(self):
        r"""Read header lines from the file and update serializer info."""
        return

    def write_header(self):
        r"""Write header lines to the file based on the serializer info."""
        # This will result in header only being sent for first message
        self.serializer.write_header = False
        return
