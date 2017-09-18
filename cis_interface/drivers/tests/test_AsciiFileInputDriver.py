import nose.tools as nt
import cis_interface.drivers.tests.test_FileInputDriver as parent


class TestAsciiFileInputParam(parent.TestFileInputParam):
    r"""Test parameters for AsciiFileInputDriver.

    Attributes (in addition to the parent class):
        -

    """

    def __init__(self, *args, **kwargs):
        super(TestAsciiFileInputParam, self).__init__(*args, **kwargs)
        self.driver = 'AsciiFileInputDriver'
        self.attr_list += ['file_kwargs', 'file']
        self.inst_kwargs['newline'] = "\n"


class TestAsciiFileInputDriverNoStart(TestAsciiFileInputParam,
                                      parent.TestFileInputDriverNoStart):
    r"""Test runner for AsciiFileInputDriver without start.

    Attributes (in addition to the parent class):
        -

    """
    pass

    
class TestAsciiFileInputDriver(TestAsciiFileInputParam,
                               parent.TestFileInputDriver):
    r"""Test runner for AsciiFileInputDriver.

    Attributes (in addition to the parent class):
        -

    """

    def assert_before_stop(self):
        r"""Assertions to make before stopping the driver instance."""
        super(parent.TestFileInputDriver, self).assert_before_stop()
        T = self.instance.start_timeout()
        while self.instance.n_ipc_msg == 0 and not T.is_out:
            self.instance.sleep()
        self.instance.stop_timeout()
        iline = 0
        while True:
            data = self.instance.ipc_recv()
            if (data is None) or (data == self.instance.eof_msg):
                break
            if len(data) > 0:
                while self.file_lines[iline].startswith(self.comment):
                    iline += 1  # pragma: no cover
                nt.assert_equal(data, self.file_lines[iline])
                iline += 1
        nt.assert_equal(len(self.file_lines), iline)
        
    def assert_after_terminate(self):
        r"""Assertions to make after stopping the driver instance."""
        super(TestAsciiFileInputDriver, self).assert_after_terminate()
        assert(not self.instance.file.is_open)
