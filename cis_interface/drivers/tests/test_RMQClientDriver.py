import unittest
from cis_interface.communication.RMQComm import _rmq_server_running
import cis_interface.drivers.tests.test_ClientDriver as parent


@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQClientParam(parent.TestClientParam):
    r"""Test parameters for RMQClientDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestRMQClientParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQClientDriver'
        self.server_comm = 'RMQComm'
        self.ocomm_name = self.server_comm

    
@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQClientDriverNoStart(TestRMQClientParam,
                                 parent.TestClientDriverNoStart):
    r"""Test class for RMQClientDriver class without start."""
    pass


@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQClientDriver(TestRMQClientParam, parent.TestClientDriver):
    r"""Test class for RMQClientDriver class."""
    pass
