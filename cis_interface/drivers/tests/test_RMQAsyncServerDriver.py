import unittest
from cis_interface.communication.RMQComm import _rmq_server_running
import cis_interface.drivers.tests.test_ServerDriver as parent


@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQAsyncServerParam(parent.TestServerParam):
    r"""Test parameters for RMQAsyncServerDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestRMQAsyncServerParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQAsyncServerDriver'
        self.client_comm = 'RMQAsyncComm'
        self.icomm_name = self.client_comm
        self.timeout = 10.0
        self.route_timeout = 60.0

    
@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQAsyncServerDriverNoStart(TestRMQAsyncServerParam,
                                      parent.TestServerDriverNoStart):
    r"""Test class for RMQAsyncServerDriver class without start."""
    pass


@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQAsyncServerDriver(TestRMQAsyncServerParam, parent.TestServerDriver):
    r"""Test class for RMQAsyncServerDriver class."""
    pass
