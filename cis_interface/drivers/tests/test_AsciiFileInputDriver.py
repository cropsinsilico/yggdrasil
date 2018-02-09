import nose.tools as nt
import cis_interface.drivers.tests.test_FileInputDriver as parent


class TestAsciiFileInputParam(parent.TestFileInputParam):
    r"""Test parameters for AsciiFileInputDriver."""

    def __init__(self, *args, **kwargs):
        super(TestAsciiFileInputParam, self).__init__(*args, **kwargs)
        self.driver = 'AsciiFileInputDriver'
        self.inst_kwargs['newline'] = "\n"
        self.icomm_name = 'AsciiFileComm'


class TestAsciiFileInputDriverNoStart(TestAsciiFileInputParam,
                                      parent.TestFileInputDriverNoStart):
    r"""Test runner for AsciiFileInputDriver without start."""
    pass

    
class TestAsciiFileInputDriver(TestAsciiFileInputParam,
                               parent.TestFileInputDriver):
    r"""Test runner for AsciiFileInputDriver."""

    def assert_before_stop(self):
        r"""Assertions to make before stopping the driver instance."""
        super(parent.TestFileInputDriver, self).assert_before_stop(
            check_open=False)
        T = self.instance.start_timeout()
        while self.recv_comm.n_msg == 0 and not T.is_out:
            self.instance.sleep()  # pragma: debug
        self.instance.stop_timeout()
        # Check file lines
        for iline, ans in enumerate(self.file_lines):
            if not ans.startswith(self.comment):
                flag, data = self.recv_comm.recv(timeout=False)
                assert(flag)
                nt.assert_equal(data, ans)
        # End of file
        flag, data = self.recv_comm.recv(timeout=False)
        assert(not flag)
        nt.assert_equal(data, self.recv_comm.eof_msg)
        assert(self.recv_comm.is_closed)
