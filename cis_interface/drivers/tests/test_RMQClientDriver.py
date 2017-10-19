import cis_interface.drivers.tests.test_ClientDriver as parent


class TestRMQClientParam(parent.TestClientParam):
    r"""Test parameters for RMQClientDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestRMQClientParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQClientDriver'
        self.server_comm = 'RMQComm'
        self.ocomm_name = self.server_comm

    
class TestRMQClientDriverNoStart(TestRMQClientParam,
                                 parent.TestClientDriverNoStart):
    r"""Test class for RMQClientDriver class without start."""
    pass


class TestRMQClientDriver(TestRMQClientParam, parent.TestClientDriver):
    r"""Test class for RMQClientDriver class."""
    pass
