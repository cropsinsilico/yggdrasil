import unittest
from cis_interface.communication.RMQComm import check_rmq_server
import cis_interface.drivers.tests.test_ServerDriver as parent


@unittest.skipIf(not check_rmq_server(), "RMQ Server not running")
class TestRMQAsyncServerParam(parent.TestServerParam):
    r"""Test parameters for RMQAsyncServerDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestRMQAsyncServerParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQAsyncServerDriver'
        self.client_comm = 'RMQAsyncComm'
        self.icomm_name = self.client_comm
        self.timeout = 10.0

    
@unittest.skipIf(not check_rmq_server(), "RMQ Server not running")
class TestRMQAsyncServerDriverNoStart(TestRMQAsyncServerParam,
                                      parent.TestServerDriverNoStart):
    r"""Test class for RMQAsyncServerDriver class without start."""
    pass


@unittest.skipIf(not check_rmq_server(), "RMQ Server not running")
class TestRMQAsyncServerDriver(TestRMQAsyncServerParam, parent.TestServerDriver):
    r"""Test class for RMQAsyncServerDriver class."""
    pass
