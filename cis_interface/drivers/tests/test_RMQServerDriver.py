import cis_interface.drivers.tests.test_ServerDriver as parent


class TestRMQServerParam(parent.TestServerParam):
    r"""Test parameters for RMQServerDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestRMQServerParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQServerDriver'
        self.client_comm = 'RMQComm'
        self.icomm_name = self.client_comm

    
class TestRMQServerDriverNoStart(TestRMQServerParam,
                                 parent.TestServerDriverNoStart):
    r"""Test class for RMQServerDriver class without start."""
    pass


class TestRMQServerDriver(TestRMQServerParam, parent.TestServerDriver):
    r"""Test class for RMQServerDriver class."""
    pass
