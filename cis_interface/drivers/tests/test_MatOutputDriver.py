import os
import cis_interface.drivers.tests.test_FileOutputDriver as parent


class TestMatOutputParam(parent.TestFileOutputParam):
    r"""Test parameters for MatOutputDriver."""

    def __init__(self, *args, **kwargs):
        super(TestMatOutputParam, self).__init__(*args, **kwargs)
        self.driver = 'MatOutputDriver'
        self.filepath = os.path.abspath('mat_input.mat')
        self.args = self.filepath
        

class TestMatOutputDriverNoStart(TestMatOutputParam,
                                 parent.TestFileOutputDriverNoStart):
    r"""Test runner for MatOutputDriver."""
    pass


class TestMatOutputDriver(TestMatOutputParam, parent.TestFileOutputDriver):
    r"""Test runner for MatOutputDriver."""

    def send_file_contents(self):
        r"""Send file contents to driver."""
        self.send_comm.send(self.data_dict)
        self.send_comm.send_eof()

    def assert_after_stop(self):
        r"""Assertions to make after stopping the driver instance."""
        super(parent.TestFileOutputDriver, self).assert_after_stop()
        assert(os.path.isfile(self.filepath))
        self.assert_equal_data_dict(self.filepath)
        #     dat_recv = loadmat(fd)
        # for k in self.data_dict.keys():
        #     np.testing.assert_array_equal(dat_recv[k], self.data_dict[k])
