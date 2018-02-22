import cis_interface.drivers.tests.test_AsciiFileOutputDriver as parent


class TestAsciiTableOutputParam(parent.TestAsciiFileOutputParam):
    r"""Test parameters for AsciiTableOutputDriver."""

    def __init__(self, *args, **kwargs):
        super(TestAsciiTableOutputParam, self).__init__(*args, **kwargs)
        self.driver = 'AsciiTableOutputDriver'
        self.inst_kwargs['column'] = '\t'
        self.inst_kwargs['format_str'] = self.fmt_str
        self.ocomm_name = 'AsciiTableComm'
        

class TestAsciiTableOutputDriverNoStart(TestAsciiTableOutputParam,
                                        parent.TestAsciiFileOutputDriverNoStart):
    r"""Test runner for AsciiTableOutputDriver without start."""
    pass
    

class TestAsciiTableOutputDriver(TestAsciiTableOutputParam,
                                 parent.TestAsciiFileOutputDriver):
    r"""Test runner for AsciiTableOutputDriver."""

    def send_file_contents(self):
        r"""Send file contents to driver."""
        self.send_comm.send_nolimit(self.fmt_str)
        for line in self.file_lines:
            self.send_comm.send_nolimit(line)
        self.send_comm.send_nolimit_eof()


class TestAsciiTableOutputDriver_Array(TestAsciiTableOutputParam,
                                       parent.TestAsciiFileOutputDriver):
    r"""Test runner for AsciiTableOutputDriver with array input."""

    def __init__(self, *args, **kwargs):
        super(TestAsciiTableOutputDriver_Array, self).__init__(*args, **kwargs)
        self.inst_kwargs['as_array'] = 'True'
        self.inst_kwargs['column_names'] = 'None'
        self.inst_kwargs['use_astropy'] = 'False'

    def send_file_contents(self):
        r"""Send file contents to driver."""
        self.send_comm.send_nolimit(self.fmt_str)
        self.send_comm.send_nolimit(self.file_bytes)
        self.send_comm.send_nolimit_eof()
