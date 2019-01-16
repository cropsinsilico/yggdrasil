import numpy as np
import pandas as pd
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

    @classmethod
    def get_testing_options(cls, as_frames=False, no_names=False):
        r"""Method to return a dictionary of testing options for this class.

        Args:
            as_frames (bool, optional): If True, the test objects will be Pandas
                data frames. Defaults to False.
            no_names (bool, optional): If True, an example is returned where the
                names are not provided to the deserializer. Defaults to False.

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
        out_seri = PandasSerialize.get_testing_options(no_names=no_names)
        out = {'kwargs': out_seri['kwargs'],
               'send': out_seri['objects'],
               'recv': [pd.concat(out_seri['objects'], ignore_index=True)],
               'dict': serialize.pandas2dict(out_seri['objects'][0]),
               'contents': out_seri['contents'],
               'msg_array': serialize.pandas2numpy(out_seri['objects'][0])}
        if not as_frames:
            out['recv'] = [serialize.pandas2list(x) for x in out['recv']]
            out['send'] = [serialize.pandas2list(x) for x in out['send']]
        out['msg'] = out['send'][0]
        for k in ['format_str', 'as_array']:
            if k in out['kwargs']:
                del out['kwargs'][k]
        return out
        
    @property
    def header_was_written(self):
        r"""bool: True if head has been written to the current file."""
        return getattr(self, '_header_was_written', False)

    @header_was_written.setter
    def header_was_written(self, header_was_written):
        r"""Set for header_was_written property."""
        if getattr(self, 'serializer', None) is not None:
            if not header_was_written:
                self.serializer.write_header = True
            else:
                self.serializer.write_header = False
        elif header_was_written:  # pragma: debug
            raise Exception("header_was_written set before serializer created")
        self._header_was_written = header_was_written

    def read_header(self):
        r"""Read header lines from the file and update serializer info."""
        return

    def write_header(self):
        r"""Write header lines to the file based on the serializer info."""
        # This will result in header only being sent for first message
        if not self.header_was_written:
            self.header_was_written = True
        return
