import nose.tools as nt
import cis_interface.drivers.tests.test_AsciiFileInputDriver as parent
import cis_interface.drivers.tests.test_FileInputDriver as super_parent


class TestAsciiTableInputParam(parent.TestAsciiFileInputParam):
    r"""Test parameters for AsciiTableInputDriver.

    Attributes (in addition to parent class's):
        -

    """

    def __init__(self, *args, **kwargs):
        super(TestAsciiTableInputParam, self).__init__(*args, **kwargs)
        self.driver = 'AsciiTableInputDriver'
        self.attr_list += ['file', 'as_array']
        self.inst_kwargs['column_names'] = None
        self.inst_kwargs['use_astropy'] = False

        
class TestAsciiTableInputDriverNoStart(TestAsciiTableInputParam,
                                       parent.TestAsciiFileInputDriverNoStart):
    r"""Test runner for AsciiTableInputDriver.

    Attributes (in addition to parent class's):
        -

    """
    pass


class TestAsciiTableInputDriver(TestAsciiTableInputParam,
                                parent.TestAsciiFileInputDriver):
    r"""Test runner for AsciiTableInputDriver.

    Attributes (in addition to parent class's):
        -

    """

    def assert_before_stop(self):
        r"""Assertions to make before stopping the driver instance."""
        super(super_parent.TestFileInputDriver, self).assert_before_stop()
        T = self.instance.start_timeout()
        while self.instance.n_ipc_msg == 0 and (not T.is_out):
            self.instance.sleep()  # pragma: debug
        self.instance.stop_timeout()
        # Format string
        data = self.instance.recv_wait()
        nt.assert_equal(data, self.fmt_str)
        # File lines
        for iline, ans in enumerate(self.file_lines):
            if not ans.startswith(self.comment):
                data = self.instance.recv_wait_nolimit()
                nt.assert_equal(data, ans)
        # End of file
        data = self.instance.recv_wait_nolimit()
        nt.assert_equal(data, self.instance.eof_msg)

        
class TestAsciiTableInputDriver_Array(TestAsciiTableInputParam,
                                      parent.TestAsciiFileInputDriver):
    r"""Test runner for AsciiTableInputDriver with array input.

    Attributes (in addition to parent class's):
        -

    """

    def __init__(self, *args, **kwargs):
        super(TestAsciiTableInputDriver_Array, self).__init__(*args, **kwargs)
        self.inst_kwargs['as_array'] = 'True'
        self.inst_kwargs['column_names'] = 'None'
        self.inst_kwargs['use_astropy'] = 'False'

    def assert_before_stop(self):
        r"""Assertions to make before stopping the driver instance."""
        super(super_parent.TestFileInputDriver, self).assert_before_stop()
        T = self.instance.start_timeout()
        while self.instance.n_ipc_msg == 0 and (not T.is_out):
            self.instance.sleep()  # pragma: debug
        self.instance.stop_timeout()
        data = self.instance.ipc_recv()
        nt.assert_equal(data, self.fmt_str)

        data = self.instance.recv_wait_nolimit()
        nt.assert_equal(data, self.file_bytes)
