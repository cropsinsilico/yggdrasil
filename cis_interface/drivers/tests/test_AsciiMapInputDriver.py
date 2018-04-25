import os
import tempfile
import nose.tools as nt
import cis_interface.drivers.tests.test_FileInputDriver as parent


class TestAsciiMapInputParam(parent.TestFileInputParam):
    r"""Test parameters for AsciiMapInputDriver."""

    def __init__(self, *args, **kwargs):
        super(TestAsciiMapInputParam, self).__init__(*args, **kwargs)
        self.driver = 'AsciiMapInputDriver'
        self.filepath = os.path.join(tempfile.gettempdir(),
                                     '%s_input.txt' % self.name)
        self.args = self.filepath
        self.icomm_name = 'AsciiMapComm'

    def setup(self):
        r"""Create a driver instance and start the driver."""
        self.write_map(self.filepath)
        # Skip writing text file by jumping up two classes
        super(parent.TestFileInputParam, self).setup()


class TestAsciiMapInputDriverNoStart(TestAsciiMapInputParam,
                                     parent.TestFileInputDriverNoStart):
    r"""Test runner for AsciiMapInputDriver without start."""
    pass


class TestAsciiMapInputDriver(TestAsciiMapInputParam,
                              parent.TestFileInputDriver):
    r"""Test runner for AsciiMapInputDriver."""

    def assert_before_stop(self):
        r"""Assertions to make before stopping the driver instance."""
        super(parent.TestFileInputDriver, self).assert_before_stop(
            check_open=False)
        self.instance.sleep()
        # File contents
        flag, msg_recv = self.recv_comm.recv(self.timeout)
        assert(flag)
        nt.assert_equal(msg_recv, self.map_dict)
        # EOF
        flag, msg_recv = self.recv_comm.recv(self.timeout)
        assert(not flag)
        nt.assert_equal(msg_recv, self.recv_comm.eof_msg)
