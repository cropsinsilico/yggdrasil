import os
import tempfile
import nose.tools as nt
import cis_interface.drivers.tests.test_FileInputDriver as parent


class TestObjFileInputParam(parent.TestFileInputParam):
    r"""Test parameters for ObjFileInputDriver."""

    def __init__(self, *args, **kwargs):
        super(TestObjFileInputParam, self).__init__(*args, **kwargs)
        self.driver = 'ObjFileInputDriver'
        self.filepath = os.path.join(tempfile.gettempdir(),
                                     '%s_input.dat' % self.name)
        self.args = self.filepath
        self.icomm_name = 'ObjFileComm'

    def setup(self):
        r"""Create a driver instance and start the driver."""
        self.write_obj(self.filepath)
        # Skip writing text file by jumping up two classes
        super(parent.TestFileInputParam, self).setup()


class TestObjFileInputDriverNoStart(TestObjFileInputParam,
                                    parent.TestFileInputDriverNoStart):
    r"""Test runner for ObjFileInputDriver without start."""
    pass


class TestObjFileInputDriver(TestObjFileInputParam,
                             parent.TestFileInputDriver):
    r"""Test runner for ObjFileInputDriver."""

    def assert_before_stop(self):
        r"""Assertions to make before stopping the driver instance."""
        super(parent.TestFileInputDriver, self).assert_before_stop(
            check_open=False)
        self.instance.sleep()
        # File contents
        flag, msg_recv = self.recv_comm.recv_nolimit(self.timeout)
        assert(flag)
        nt.assert_equal(msg_recv, self.obj_dict)
        # EOF
        flag, msg_recv = self.recv_comm.recv_nolimit(self.timeout)
        assert(not flag)
        nt.assert_equal(msg_recv, self.recv_comm.eof_msg)
