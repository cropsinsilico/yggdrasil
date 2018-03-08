import cis_interface.drivers.tests.test_FileOutputDriver as parent


class TestAsciiFileOutputParam(parent.TestFileOutputParam):
    r"""Test parameters for AsciiFileOutputDriver.

    Attributes (in addition to parent class's):
        -

    """

    def __init__(self, *args, **kwargs):
        super(TestAsciiFileOutputParam, self).__init__(*args, **kwargs)
        self.driver = 'AsciiFileOutputDriver'
        self.inst_kwargs['newline'] = "\n"
        self.ocomm_name = 'AsciiFileComm'


class TestAsciiFileOutputDriverNoStart(TestAsciiFileOutputParam,
                                       parent.TestFileOutputDriverNoStart):
    r"""Test runner for AsciiFileOutputDriver without start.

    Attributes (in addition to parent class's):
        -

    """
    pass


class TestAsciiFileOutputDriver(TestAsciiFileOutputParam,
                                parent.TestFileOutputDriver):
    r"""Test runner for AsciiFileOutputDriver.

    Attributes (in addition to parent class's):
        -

    """

    def send_file_contents(self):
        r"""Send file contents to driver."""
        self.send_comm.send(self.fmt_str_line)
        for line in self.file_lines:
            self.send_comm.send(line)
        self.send_comm.send_eof()
