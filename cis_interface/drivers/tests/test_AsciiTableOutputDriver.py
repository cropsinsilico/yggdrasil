from cis_interface import backwards
import cis_interface.drivers.tests.test_AsciiFileOutputDriver as parent


class TestAsciiTableOutputParam(parent.TestAsciiFileOutputParam):
    r"""Test parameters for AsciiTableOutputDriver."""

    ocomm_name = 'AsciiTableComm'
        

class TestAsciiTableOutputDriverNoStart(TestAsciiTableOutputParam,
                                        parent.TestAsciiFileOutputDriverNoStart):
    r"""Test runner for AsciiTableOutputDriver without start."""
    pass
    

class TestAsciiTableOutputDriver(TestAsciiTableOutputParam,
                                 parent.TestAsciiFileOutputDriver):
    r"""Test runner for AsciiTableOutputDriver."""
    pass


class TestAsciiTableOutputDriver_Array(TestAsciiTableOutputParam,
                                       parent.TestAsciiFileOutputDriver):
    r"""Test runner for AsciiTableOutputDriver with array input."""

    testing_option_kws = {'as_array': True}
