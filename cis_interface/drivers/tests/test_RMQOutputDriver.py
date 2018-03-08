import unittest
from cis_interface.communication.RMQComm import _rmq_server_running
import cis_interface.drivers.tests.test_ConnectionDriver as parent


@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQOutputParam(parent.TestConnectionParam):
    r"""Test parameters for RMQOutputDriver."""

    def __init__(self, *args, **kwargs):
        super(TestRMQOutputParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQOutputDriver'
        self.args = 'test'
        self.ocomm_name = 'RMQComm'
        

@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQOutputDriverNoStart(TestRMQOutputParam,
                                 parent.TestConnectionDriverNoStart):
    r"""Test runner for RMQOutputDriver without start."""
    pass


@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQOutputDriver(TestRMQOutputParam,
                          parent.TestConnectionDriver):
    r"""Test runner for RMQOutputDriver."""
    pass
