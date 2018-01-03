import cis_interface.drivers.tests.test_ServerDriver as parent


class TestRMQAsyncServerParam(parent.TestServerParam):
    r"""Test parameters for RMQAsyncServerDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestRMQAsyncServerParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQAsyncServerDriver'
        self.client_comm = 'RMQAsyncComm'
        self.icomm_name = self.client_comm
        self.timeout = 3.0

    
class TestRMQAsyncServerDriverNoStart(TestRMQAsyncServerParam,
                                      parent.TestServerDriverNoStart):
    r"""Test class for RMQAsyncServerDriver class without start."""
    pass


class TestRMQAsyncServerDriver(TestRMQAsyncServerParam, parent.TestServerDriver):
    r"""Test class for RMQAsyncServerDriver class."""
    pass
