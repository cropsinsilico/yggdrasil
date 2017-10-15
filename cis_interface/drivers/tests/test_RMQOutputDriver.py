import nose.tools as nt
import cis_interface.drivers.tests.test_ConnectionDriver as parent


class TestRMQOutputParam(parent.TestConnectionParam):
    r"""Test parameters for RMQOutputDriver."""

    def __init__(self, *args, **kwargs):
        super(TestRMQOutputParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQOutputDriver'
        self.args = 'test'
        self.ocomm_name = 'RMQComm'
        

class TestRMQOutputDriverNoStart(TestRMQOutputParam,
                                 parent.TestConnectionDriverNoStart):
    r"""Test runner for RMQOutputDriver without start."""
    pass


class TestRMQOutputDriver(TestRMQOutputParam,
                          parent.TestConnectionDriver):
    r"""Test runner for RMQOutputDriver."""
    pass
