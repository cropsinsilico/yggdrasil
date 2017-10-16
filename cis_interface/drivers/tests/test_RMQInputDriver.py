import cis_interface.drivers.tests.test_ConnectionDriver as parent


class TestRMQInputParam(parent.TestConnectionParam):
    r"""Test parameters for RMQInputDriver."""

    def __init__(self, *args, **kwargs):
        super(TestRMQInputParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQInputDriver'
        self.args = 'test'
        self.icomm_name = 'RMQComm'

        
class TestRMQInputDriverNoStart(TestRMQInputParam,
                                parent.TestConnectionDriverNoStart):
    r"""Test runner for RMQInputDriver without start."""
    pass


class TestRMQInputDriver(TestRMQInputParam, parent.TestConnectionDriver):
    r"""Test runner for RMQInputDriver."""
    pass
