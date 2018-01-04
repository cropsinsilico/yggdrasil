import unittest
from cis_interface.communication.RMQComm import check_rmq_server
import cis_interface.drivers.tests.test_ClientDriver as parent


@unittest.skipIf(not check_rmq_server(), "RMQ Server not running")
class TestRMQAsyncClientParam(parent.TestClientParam):
    r"""Test parameters for RMQAsyncClientDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestRMQAsyncClientParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQAsyncClientDriver'
        self.server_comm = 'RMQAsyncComm'
        self.ocomm_name = self.server_comm
        self.timeout = 10.0

    
@unittest.skipIf(not check_rmq_server(), "RMQ Server not running")
class TestRMQAsyncClientDriverNoStart(TestRMQAsyncClientParam,
                                      parent.TestClientDriverNoStart):
    r"""Test class for RMQAsyncClientDriver class without start."""
    pass


@unittest.skipIf(not check_rmq_server(), "RMQ Server not running")
class TestRMQAsyncClientDriver(TestRMQAsyncClientParam, parent.TestClientDriver):
    r"""Test class for RMQAsyncClientDriver class."""
    pass
