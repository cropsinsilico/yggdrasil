import os
import nose.tools as nt
import tempfile
import cis_interface.drivers.tests.test_FileOutputDriver as parent


class TestObjFileOutputParam(parent.TestFileOutputParam):
    r"""Test parameters for ObjFileOutputDriver."""

    def __init__(self, *args, **kwargs):
        super(TestObjFileOutputParam, self).__init__(*args, **kwargs)
        self.driver = 'ObjFileOutputDriver'
        self.filepath = os.path.join(tempfile.gettempdir(),
                                     '%s_output.dat' % self.name)
        self.args = self.filepath
        self.ocomm_name = 'ObjFileComm'


class TestObjFileOutputDriverNoStart(TestObjFileOutputParam,
                                     parent.TestFileOutputDriverNoStart):
    r"""Test runner for ObjFileOutputDriver without start."""
    pass


class TestObjFileOutputDriver(TestObjFileOutputParam,
                              parent.TestFileOutputDriver):
    r"""Test runner for ObjFileOutputDriver."""

    def send_file_contents(self):
        r"""Send file contents to driver."""
        self.send_comm.send_nolimit(self.obj_dict)
        self.send_comm.send_eof()

    def assert_after_stop(self):
        r"""Assertions to make after stopping the driver instance."""
        super(parent.TestFileOutputDriver, self).assert_after_stop()
        assert(os.path.isfile(self.filepath))
        with open(self.filepath, 'rb') as fd:
            contents = fd.read()
        nt.assert_equal(contents, self.obj_file_contents)
