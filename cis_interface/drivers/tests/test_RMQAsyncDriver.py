import unittest
from cis_interface.communication.RMQComm import _rmq_server_running
import cis_interface.drivers.tests.test_RMQAsyncCommDriver as parent


@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQAsyncParam(parent.TestRMQAsyncCommParam):
    r"""Test parameters for RMQAsyncDriver class."""
    pass

        
@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQAsyncDriverNoStart(parent.TestRMQAsyncCommDriverNoStart):
    r"""Test class for RMQAsyncDriver class without start."""
    pass


@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQAsyncDriver(parent.TestRMQAsyncCommDriver):
    r"""Test class for RMQAsyncDriver class."""
    pass
