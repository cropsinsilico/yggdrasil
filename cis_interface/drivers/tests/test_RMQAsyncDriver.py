import unittest
from cis_interface.communication.RMQComm import check_rmq_server
import cis_interface.drivers.tests.test_RMQAsyncCommDriver as parent


@unittest.skipIf(not check_rmq_server(), "RMQ Server not running")
class TestRMQAsyncParam(parent.TestRMQAsyncCommParam):
    r"""Test parameters for RMQAsyncDriver class."""
    pass

        
@unittest.skipIf(not check_rmq_server(), "RMQ Server not running")
class TestRMQAsyncDriverNoStart(parent.TestRMQAsyncCommDriverNoStart):
    r"""Test class for RMQAsyncDriver class without start."""
    pass


@unittest.skipIf(not check_rmq_server(), "RMQ Server not running")
class TestRMQAsyncDriver(parent.TestRMQAsyncCommDriver):
    r"""Test class for RMQAsyncDriver class."""
    pass
