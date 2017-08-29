import nose.tools as nt
import test_FileInputDriver as parent


class TestAsciiFileInputDriver(parent.TestFileInputDriver):
    r"""Test runner for AsciiFileInputDriver."""

    def __init__(self):
        super(TestAsciiFileInputDriver, self).__init__()
        self.driver = 'AsciiFileInputDriver'
        self.attr_list += ['file_kwargs', 'file']

    def assert_before_stop(self):
        r"""Assertions to make before stopping the driver instance."""
        super(parent.TestFileInputDriver, self).assert_before_stop()
        while self.instance.n_msg == 0:
            self.instance.sleep()
        iline = 0
        while True:
            data = self.instance.ipc_recv()
            if (data is None) or (data == self.instance.eof_msg):
                break
            if len(data) > 0:
                while self.file_lines[iline].startswith('#'):
                    iline += 1  # pragma: no cover
                nt.assert_equal(data, self.file_lines[iline])
                iline += 1
        nt.assert_equal(len(self.file_lines), iline)
        
    def assert_after_terminate(self):
        r"""Assertions to make after stopping the driver instance."""
        super(TestAsciiFileInputDriver, self).assert_after_terminate()
        assert(not self.instance.file.is_open)
