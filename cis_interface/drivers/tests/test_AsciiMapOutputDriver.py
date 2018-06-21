import os
import tempfile
import cis_interface.drivers.tests.test_FileOutputDriver as parent


class TestAsciiMapOutputParam(parent.TestFileOutputParam):
    r"""Test parameters for AsciiMapOutputDriver."""

    def __init__(self, *args, **kwargs):
        super(TestAsciiMapOutputParam, self).__init__(*args, **kwargs)
        self.driver = 'AsciiMapOutputDriver'
        self.filepath = os.path.join(tempfile.gettempdir(),
                                     '%s_output.txt' % self.name)
        self.args = self.filepath
        self.ocomm_name = 'AsciiMapComm'


class TestAsciiMapOutputDriverNoStart(TestAsciiMapOutputParam,
                                      parent.TestFileOutputDriverNoStart):
    r"""Test runner for AsciiMapOutputDriver without start."""
    pass


class TestAsciiMapOutputDriver(TestAsciiMapOutputParam,
                               parent.TestFileOutputDriver):
    r"""Test runner for AsciiMapOutputDriver."""

    def send_file_contents(self):
        r"""Send file contents to driver."""
        self.send_comm.send(self.map_dict)
        self.send_comm.send_eof()

    @property
    def contents_to_read(self):
        r"""str: Contents that should be read to the file."""
        return self.mapfile_contents
