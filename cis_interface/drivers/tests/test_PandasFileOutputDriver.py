import numpy as np
from cis_interface import serialize
import cis_interface.drivers.tests.test_FileOutputDriver as parent


class TestPandasFileOutputParam(parent.TestFileOutputParam):
    r"""Test parameters for PandasFileOutputDriver."""

    def __init__(self, *args, **kwargs):
        super(TestPandasFileOutputParam, self).__init__(*args, **kwargs)
        self.driver = 'PandasFileOutputDriver'
        self.inst_kwargs['delimiter'] = self.delimiter
        self.ocomm_name = 'PandasFileComm'

    @property
    def send_comm_kwargs(self):
        r"""dict: Keyword arguments for send comm."""
        out = super(TestPandasFileOutputParam, self).send_comm_kwargs
        out['serializer'] = None
        out['serializer_kwargs'] = {'format_str': self.fmt_str,
                                    'field_names': self.field_names,
                                    'field_units': self.field_units,
                                    'as_array': True}
        out['send_converter'] = serialize.pandas2numpy
        return out

    @property
    def msg_short(self):  # pragma: debug
        r"""pandas.DataFrame: Pandas data frame."""
        return self.pandas_frame
    
    @property
    def msg_long(self):  # pragma: debug
        r"""pandas.DataFrame: Pandas data frame."""
        return self.pandas_frame

    def assert_msg_equal(self, x, y):  # pragma: debug
        r"""Assert that two messages are equivalent."""
        np.testing.assert_array_equal(x, y)

    @property
    def contents_to_read(self):
        r"""str: Contents that should be read to the file."""
        return self.pandas_file_contents


class TestPandasFileOutputDriverNoStart(TestPandasFileOutputParam,
                                        parent.TestFileOutputDriverNoStart):
    r"""Test runner for PandasFileOutputDriver without start."""
    pass
    

class TestPandasFileOutputDriver(TestPandasFileOutputParam,
                                 parent.TestFileOutputDriver):
    r"""Test runner for PandasFileOutputDriver."""

    def send_file_contents(self):
        r"""Send file contents to driver."""
        self.send_comm.send(self.pandas_frame)
        self.send_comm.send_eof()
