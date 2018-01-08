import os
import nose.tools as nt
import cis_interface.drivers.tests.test_FileInputDriver as parent


class TestMatInputParam(parent.TestFileInputParam):
    r"""Test runner for MatInputDriver."""

    def __init__(self, *args, **kwargs):
        super(TestMatInputParam, self).__init__(*args, **kwargs)
        self.driver = 'MatInputDriver'
        self.filepath = os.path.abspath('mat_input.mat')
        self.args = self.filepath

    def setup(self):
        r"""Create a driver instance and start the driver."""
        with open(self.filepath, 'wb') as fd:
            fd.write(self.mat_data)
        super(parent.TestFileInputParam, self).setup()
        

class TestMatInputDriverNoStart(TestMatInputParam,
                                parent.TestFileInputDriverNoStart):
    r"""Test runner for MatInputDriver without start."""
    pass


class TestMatInputDriver(TestMatInputParam, parent.TestFileInputDriver):
    r"""Test runner for MatInputDriver."""
    
    def assert_before_stop(self):
        r"""Assertions to make before stopping the driver instance."""
        super(parent.TestFileInputDriver, self).assert_before_stop(
            check_open=False)
        self.instance.sleep()
        # File contents
        flag, msg_recv = self.recv_comm.recv(self.timeout)
        assert(flag)
        self.assert_equal_data_dict(msg_recv)
        # EOF
        flag, msg_recv = self.recv_comm.recv(self.timeout)
        assert(not flag)
        nt.assert_equal(msg_recv, self.recv_comm.eof_msg)
