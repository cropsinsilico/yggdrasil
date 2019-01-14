import nose.tools as nt
import cis_interface.drivers.tests.test_FileInputDriver as parent


class TestAsciiFileInputParam(parent.TestFileInputParam):
    r"""Test parameters for AsciiFileInputDriver."""

    icomm_name = 'AsciiFileComm'

    def __init__(self, *args, **kwargs):
        super(TestAsciiFileInputParam, self).__init__(*args, **kwargs)
        self.inst_kwargs['newline'] = "\n"


class TestAsciiFileInputDriverNoStart(TestAsciiFileInputParam,
                                      parent.TestFileInputDriverNoStart):
    r"""Test runner for AsciiFileInputDriver without start."""
    pass

    
class TestAsciiFileInputDriver(TestAsciiFileInputParam,
                               parent.TestFileInputDriver):
    r"""Test runner for AsciiFileInputDriver."""
    pass
