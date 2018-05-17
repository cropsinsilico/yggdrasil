import os
import nose.tools as nt
import tempfile
import cis_interface.drivers.tests.test_FileOutputDriver as parent


class TestPlyFileOutputParam(parent.TestFileOutputParam):
    r"""Test parameters for PlyFileOutputDriver."""

    def __init__(self, *args, **kwargs):
        super(TestPlyFileOutputParam, self).__init__(*args, **kwargs)
        self.driver = 'PlyFileOutputDriver'
        self.filepath = os.path.join(tempfile.gettempdir(),
                                     '%s_output.dat' % self.name)
        self.args = self.filepath
        self.ocomm_name = 'PlyFileComm'


class TestPlyFileOutputDriverNoStart(TestPlyFileOutputParam,
                                     parent.TestFileOutputDriverNoStart):
    r"""Test runner for PlyFileOutputDriver without start."""
    pass


class TestPlyFileOutputDriver(TestPlyFileOutputParam,
                              parent.TestFileOutputDriver):
    r"""Test runner for PlyFileOutputDriver."""

    def send_file_contents(self):
        r"""Send file contents to driver."""
        self.send_comm.send_nolimit(self.ply_dict)
        self.send_comm.send_eof()

    def assert_after_stop(self):
        r"""Assertions to make after stopping the driver instance."""
        super(parent.TestFileOutputDriver, self).assert_after_stop()
        assert(os.path.isfile(self.filepath))
        with open(self.filepath, 'rb') as fd:
            contents = fd.read()
        nt.assert_equal(contents, self.ply_file_contents)
