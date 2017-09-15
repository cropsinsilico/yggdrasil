import cis_interface.drivers.tests.test_FileOutputDriver as parent


class TestAsciiFileOutputParam(parent.TestFileOutputParam):
    r"""Test parameters for AsciiFileOutputDriver.

    Attributes (in addition to parent class's):
        -

    """

    def __init__(self, *args, **kwargs):
        super(TestAsciiFileOutputParam, self).__init__(*args, **kwargs)
        self.driver = 'AsciiFileOutputDriver'
        self.attr_list += ['file_kwargs', 'file']
        self.inst_kwargs['newline'] = "\n"


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
