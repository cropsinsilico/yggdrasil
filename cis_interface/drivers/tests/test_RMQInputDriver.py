import unittest
from cis_interface.communication.RMQComm import _rmq_server_running
import cis_interface.drivers.tests.test_ConnectionDriver as parent


@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQInputParam(parent.TestConnectionParam):
    r"""Test parameters for RMQInputDriver."""

    def __init__(self, *args, **kwargs):
        super(TestRMQInputParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQInputDriver'
        self.args = 'test'
        self.icomm_name = 'RMQComm'

        
@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQInputDriverNoStart(TestRMQInputParam,
                                parent.TestConnectionDriverNoStart):
    r"""Test runner for RMQInputDriver without start."""
    pass


@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQInputDriver(TestRMQInputParam, parent.TestConnectionDriver):
    r"""Test runner for RMQInputDriver."""
    pass
