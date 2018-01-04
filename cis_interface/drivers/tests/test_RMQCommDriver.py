import unittest
from cis_interface.communication.RMQComm import check_rmq_server
from cis_interface.drivers.tests import test_CommDriver as parent


@unittest.skipIf(not check_rmq_server(), "RMQ Server not running")
class TestRMQCommParam(parent.TestCommParam):
    r"""Test parameters for the RMQCommDriver class."""
    def __init__(self, *args, **kwargs):
        super(TestRMQCommParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQCommDriver'
        self.comm_name = 'RMQComm'
    

@unittest.skipIf(not check_rmq_server(), "RMQ Server not running")
class TestRMQCommDriverNoStart(TestRMQCommParam, parent.TestCommDriverNoStart):
    r"""Test class for the RMQCommDriver class without start."""
    pass


@unittest.skipIf(not check_rmq_server(), "RMQ Server not running")
class TestRMQCommDriver(TestRMQCommParam, parent.TestCommDriver):
    r"""Test class for the RMQCommDriver class."""
    pass
