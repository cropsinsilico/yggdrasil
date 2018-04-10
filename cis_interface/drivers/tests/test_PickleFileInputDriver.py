import os
import tempfile
import nose.tools as nt
import cis_interface.drivers.tests.test_FileInputDriver as parent


class TestPickleFileInputParam(parent.TestFileInputParam):
    r"""Test parameters for PickleFileInputDriver."""

    def __init__(self, *args, **kwargs):
        super(TestPickleFileInputParam, self).__init__(*args, **kwargs)
        self.driver = 'PickleFileInputDriver'
        self.filepath = os.path.join(tempfile.gettempdir(),
                                     '%s_input.dat' % self.name)
        self.args = self.filepath
        self.icomm_name = 'PickleFileComm'

    def setup(self):
        r"""Create a driver instance and start the driver."""
        self.write_pickle(self.filepath)
        # Skip writing text file by jumping up two classes
        super(parent.TestFileInputParam, self).setup()


class TestPickleFileInputDriverNoStart(TestPickleFileInputParam,
                                       parent.TestFileInputDriverNoStart):
    r"""Test runner for PickleFileInputDriver without start."""
    pass


class TestPickleFileInputDriver(TestPickleFileInputParam,
                                parent.TestFileInputDriver):
    r"""Test runner for PickleFileInputDriver."""

    def assert_before_stop(self):
        r"""Assertions to make before stopping the driver instance."""
        super(parent.TestFileInputDriver, self).assert_before_stop(
            check_open=False)
        self.instance.sleep()
        # File contents
        flag, msg_recv = self.recv_comm.recv_nolimit(self.timeout)
        assert(flag)
        self.assert_equal_data_dict(msg_recv)
        # EOF
        flag, msg_recv = self.recv_comm.recv_nolimit(self.timeout)
        assert(not flag)
        nt.assert_equal(msg_recv, self.recv_comm.eof_msg)
