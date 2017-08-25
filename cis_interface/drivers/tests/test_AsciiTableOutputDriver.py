import nose.tools as nt
import test_AsciiFileOutputDriver as parent
import test_FileOutputDriver as super_parent


class TestAsciiTableOutputDriver(parent.TestAsciiFileOutputDriver):
    r"""Test runner for AsciiTableOutputDriver."""

    def __init__(self):
        super(TestAsciiTableOutputDriver, self).__init__()
        self.driver = 'AsciiTableOutputDriver'
        self.attr_list = ['file', 'as_array']

    def setup(self):
        r"""Create a driver instance and start the driver."""
        super(super_parent.TestFileOutputDriver, self).setup()
        self.instance.ipc_send(self.fmt_str)
        for line in self.file_lines:
            self.instance.ipc_send_nolimit(line)
        self.instance.ipc_send_nolimit(self.instance.eof_msg)


class TestAsciiTableOutputDriver_Array(parent.TestAsciiFileOutputDriver):
    r"""Test runner for AsciiTableOutputDriver with array input."""

    def __init__(self):
        super(TestAsciiTableOutputDriver_Array, self).__init__()
        self.driver = 'AsciiTableOutputDriver'
        self.attr_list = ['file', 'as_array']
        self.args = {'filepath': self.filepath,
                     'as_array': True}

    def setup(self):
        r"""Create a driver instance and start the driver."""
        super(super_parent.TestFileOutputDriver, self).setup()
        self.instance.ipc_send(self.fmt_str)
        self.instance.ipc_send_nolimit(self.file_bytes)
        self.instance.ipc_send_nolimit(self.instance.eof_msg)
