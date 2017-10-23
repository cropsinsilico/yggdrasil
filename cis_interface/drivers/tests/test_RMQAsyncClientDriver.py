import cis_interface.drivers.tests.test_ClientDriver as parent


class TestRMQAsyncClientParam(parent.TestClientParam):
    r"""Test parameters for RMQAsyncClientDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestRMQAsyncClientParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQAsyncClientDriver'
        self.server_comm = 'RMQAsyncComm'
        self.ocomm_name = self.server_comm

    
class TestRMQAsyncClientDriverNoStart(TestRMQAsyncClientParam,
                                      parent.TestClientDriverNoStart):
    r"""Test class for RMQAsyncClientDriver class without start."""
    pass


class TestRMQAsyncClientDriver(TestRMQAsyncClientParam, parent.TestClientDriver):
    r"""Test class for RMQAsyncClientDriver class."""
    pass
