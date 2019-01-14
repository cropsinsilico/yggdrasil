import cis_interface.drivers.tests.test_FileOutputDriver as parent


class TestAsciiFileOutputParam(parent.TestFileOutputParam):
    r"""Test parameters for AsciiFileOutputDriver."""

    ocomm_name = 'AsciiFileComm'
    
    def __init__(self, *args, **kwargs):
        super(TestAsciiFileOutputParam, self).__init__(*args, **kwargs)
        self.inst_kwargs['newline'] = "\n"


class TestAsciiFileOutputDriverNoStart(TestAsciiFileOutputParam,
                                       parent.TestFileOutputDriverNoStart):
    r"""Test runner for AsciiFileOutputDriver without start."""
    pass


class TestAsciiFileOutputDriver(TestAsciiFileOutputParam,
                                parent.TestFileOutputDriver):
    r"""Test runner for AsciiFileOutputDriver."""
    pass
