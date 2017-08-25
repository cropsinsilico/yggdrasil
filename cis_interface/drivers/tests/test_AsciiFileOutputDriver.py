import test_FileOutputDriver as parent


class TestAsciiFileOutputDriver(parent.TestFileOutputDriver):
    r"""Test runner for AsciiFileOutputDriver."""

    def __init__(self):
        super(TestAsciiFileOutputDriver, self).__init__()
        self.driver = 'AsciiFileOutputDriver'
        self.attr_list += ['file_kwargs', 'file']

    def setup(self):
        r"""Create a driver instance and start the driver."""
        super(parent.TestFileOutputDriver, self).setup()
        self.instance.ipc_send(self.fmt_str_line)
        for line in self.file_lines:
            self.instance.ipc_send(line)
        self.instance.ipc_send(self.instance.eof_msg)

    def assert_after_terminate(self):
        r"""Assertions to make after stopping the driver instance."""
        super(TestAsciiFileOutputDriver, self).assert_after_terminate()
        assert(not self.instance.file.is_open)
        
