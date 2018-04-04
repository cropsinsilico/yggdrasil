import unittest
from cis_interface.communication.RMQComm import _rmq_server_running
from cis_interface.drivers.tests import test_CommDriver as parent


@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQAsyncCommParam(parent.TestCommParam):
    r"""Test parameters for the RMQAsyncCommDriver class."""
    def __init__(self, *args, **kwargs):
        super(TestRMQAsyncCommParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQAsyncCommDriver'
        self.comm_name = 'RMQAsyncComm'
        self._cleanup_comm_call = self.comm_name
    

@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQAsyncCommDriverNoStart(TestRMQAsyncCommParam,
                                    parent.TestCommDriverNoStart):
    r"""Test class for the RMQAsyncCommDriver class without start."""
    pass


@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQAsyncCommDriver(TestRMQAsyncCommParam, parent.TestCommDriver):
    r"""Test class for the RMQAsyncCommDriver class."""
    pass
