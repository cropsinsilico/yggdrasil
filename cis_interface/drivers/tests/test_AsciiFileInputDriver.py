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
            self.instance.sleep()  # pragma: debug
        self.instance.stop_timeout()
        # Check file lines
        for iline, ans in enumerate(self.file_lines):
            if not ans.startswith(self.comment):
                data = self.instance.recv_wait()
                nt.assert_equal(data, ans)
        # End of file
        data = self.instance.recv_wait()
        nt.assert_equal(data, self.instance.eof_msg)
        
    def assert_after_terminate(self):
        r"""Assertions to make after stopping the driver instance."""
        super(TestAsciiFileInputDriver, self).assert_after_terminate()
        assert(not self.instance.file.is_open)
