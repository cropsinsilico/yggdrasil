import numpy as np
import nose.tools as nt
from cis_interface import backwards, units
import cis_interface.drivers.tests.test_AsciiFileInputDriver as parent
import cis_interface.drivers.tests.test_FileInputDriver as super_parent


class TestAsciiTableInputParam(parent.TestAsciiFileInputParam):
    r"""Test parameters for AsciiTableInputDriver."""
    def __init__(self, *args, **kwargs):
        super(TestAsciiTableInputParam, self).__init__(*args, **kwargs)
        self.driver = 'AsciiTableInputDriver'
        self.inst_kwargs['field_names'] = None
        self.inst_kwargs['use_astropy'] = False
        self.icomm_name = 'AsciiTableComm'

    @property
    def msg_short(self):  # pragma: debug
        r"""str: Always use file lines as message."""
        return self.file_rows[0]
    
    @property
    def msg_long(self):  # pragma: debug
        r"""str: Always use file lines as message."""
        return self.file_rows[0]

        
class TestAsciiTableInputDriverNoStart(TestAsciiTableInputParam,
                                       parent.TestAsciiFileInputDriverNoStart):
    r"""Test runner for AsciiTableInputDriver."""
    pass


class TestAsciiTableInputDriver(TestAsciiTableInputParam,
                                parent.TestAsciiFileInputDriver):
    r"""Test runner for AsciiTableInputDriver."""

    def assert_before_stop(self):
        r"""Assertions to make before stopping the driver instance."""
        super(super_parent.TestFileInputDriver, self).assert_before_stop(
            check_open=False)
        T = self.instance.start_timeout()
        while self.recv_comm.n_msg == 0 and (not T.is_out):
            self.instance.sleep()  # pragma: debug
        self.instance.stop_timeout()
        # File lines
        for ans in self.file_rows:
            flag, data = self.recv_comm.recv_nolimit(timeout=False)
            assert(flag)
            self.assert_msg_equal(data, ans)
        # End of file
        flag, data = self.recv_comm.recv_nolimit(timeout=False)
        assert(not flag)
        nt.assert_equal(data, self.recv_comm.eof_msg)

        
class TestAsciiTableInputDriver_Array(TestAsciiTableInputParam,
                                      parent.TestAsciiFileInputDriver):
    r"""Test runner for AsciiTableInputDriver with array input."""

    def __init__(self, *args, **kwargs):
        super(TestAsciiTableInputDriver_Array, self).__init__(*args, **kwargs)
        self.inst_kwargs['as_array'] = True
        field_names = [backwards.bytes2unicode(n) for n in self.field_names]
        field_units = [backwards.bytes2unicode(n) for n in self.field_units]
        self.inst_kwargs['field_names'] = field_names
        self.inst_kwargs['field_units'] = field_units
        self.inst_kwargs['use_astropy'] = False

    @property
    def msg_short(self):  # pragma: debug
        r"""str: Always use file bytes as message."""
        return self.file_array_units
    
    @property
    def msg_long(self):  # pragma: debug
        r"""str: Always use file bytes as message."""
        return self.file_array_units

    def assert_msg_equal(self, x, y):
        r"""Assert that two messages are equal."""
        if isinstance(x, np.ndarray):
            x = [x[n] for n in x.dtype.names]
        if isinstance(y, np.ndarray):
            y = [y[n] for n in y.dtype.names]
        assert(isinstance(x, (list, tuple)))
        assert(isinstance(y, (list, tuple)))
        nt.assert_equal(len(x), len(y))
        for ix, iy in zip(x, y):
            np.testing.assert_array_equal(units.get_data(ix),
                                          units.get_data(iy))

    def assert_before_stop(self):
        r"""Assertions to make before stopping the driver instance."""
        super(super_parent.TestFileInputDriver, self).assert_before_stop(
            check_open=False)
        T = self.instance.start_timeout()
        while self.recv_comm.n_msg == 0 and (not T.is_out):
            self.instance.sleep()  # pragma: debug
        self.instance.stop_timeout()
        # Array
        flag, data = self.recv_comm.recv_nolimit(self.timeout)
        assert(flag)
        self.assert_msg_equal(data, self.msg_short)
        # End of file
        flag, data = self.recv_comm.recv_nolimit(self.timeout)
        assert(not flag)
        nt.assert_equal(data, self.recv_comm.eof_msg)
        assert(self.recv_comm.is_closed)
