import unittest
from cis_interface.communication.RMQComm import _rmq_server_running
import cis_interface.drivers.tests.test_ServerDriver as parent


@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQServerParam(parent.TestServerParam):
    r"""Test parameters for RMQServerDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestRMQServerParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQServerDriver'
        self.client_comm = 'RMQComm'
        self.icomm_name = self.client_comm

    
@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQServerDriverNoStart(TestRMQServerParam,
                                 parent.TestServerDriverNoStart):
    r"""Test class for RMQServerDriver class without start."""
    pass


@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQServerDriver(TestRMQServerParam, parent.TestServerDriver):
    r"""Test class for RMQServerDriver class."""
    pass
