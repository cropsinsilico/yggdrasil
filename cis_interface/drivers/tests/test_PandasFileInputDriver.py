import numpy as np
import nose.tools as nt
from cis_interface import serialize
import cis_interface.drivers.tests.test_FileInputDriver as parent


class TestPandasFileInputParam(parent.TestFileInputParam):
    r"""Test parameters for PandasFileInputDriver."""
    def __init__(self, *args, **kwargs):
        super(TestPandasFileInputParam, self).__init__(*args, **kwargs)
        self.driver = 'PandasFileInputDriver'
        self.inst_kwargs['delimiter'] = self.delimiter
        self.icomm_name = 'PandasFileComm'

    @property
    def contents_to_write(self):
        r"""Contents that should be written to the file."""
        return self.pandas_file_contents

    @property
    def recv_comm_kwargs(self):
        r"""dict: Keyword arguments for recv comm."""
        out = super(TestPandasFileInputParam, self).recv_comm_kwargs
        out['recv_converter'] = serialize.numpy2pandas
        return out

    @property
    def msg_short(self):  # pragma: debug
        r"""pandas.DataFrame: Pandas data frame."""
        return self.pandas_frame
    
    @property
    def msg_long(self):  # pragma: debug
        r"""pandas.DataFrame: Pandas data frame."""
        return self.pandas_frame

    def assert_msg_equal(self, x, y):
        r"""Assert that two messages are equivalent."""
        np.testing.assert_array_equal(x, y)

        
class TestPandasFileInputDriverNoStart(TestPandasFileInputParam,
                                       parent.TestFileInputDriverNoStart):
    r"""Test runner for PandasFileInputDriver."""
    pass


class TestPandasFileInputDriver(TestPandasFileInputParam,
                                parent.TestFileInputDriver):
    r"""Test runner for PandasFileInputDriver."""

    def assert_before_stop(self):
        r"""Assertions to make before stopping the driver instance."""
        super(parent.TestFileInputDriver, self).assert_before_stop(
            check_open=False)
        T = self.instance.start_timeout()
        while self.recv_comm.n_msg == 0 and (not T.is_out):
            self.instance.sleep()  # pragma: debug
        self.instance.stop_timeout()
        # File contents
        flag, data = self.recv_comm.recv_nolimit(timeout=False)
        assert(flag)
        self.assert_msg_equal(data, self.pandas_frame)
        # End of file
        flag, data = self.recv_comm.recv_nolimit(timeout=False)
        assert(not flag)
        nt.assert_equal(data, self.recv_comm.eof_msg)
        assert(self.recv_comm.is_closed)
