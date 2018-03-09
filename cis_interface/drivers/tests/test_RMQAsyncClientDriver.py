import unittest
from cis_interface.communication.RMQComm import _rmq_server_running
import cis_interface.drivers.tests.test_ClientDriver as parent


@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQAsyncClientParam(parent.TestClientParam):
    r"""Test parameters for RMQAsyncClientDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestRMQAsyncClientParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQAsyncClientDriver'
        self.server_comm = 'RMQAsyncComm'
        self.ocomm_name = self.server_comm
        self.timeout = 10.0
        self.route_timeout = 60.0

    
@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQAsyncClientDriverNoStart(TestRMQAsyncClientParam,
                                      parent.TestClientDriverNoStart):
    r"""Test class for RMQAsyncClientDriver class without start."""
    pass


@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQAsyncClientDriver(TestRMQAsyncClientParam, parent.TestClientDriver):
    r"""Test class for RMQAsyncClientDriver class."""
    pass
