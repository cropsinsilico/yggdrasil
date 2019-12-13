import unittest
import flaky
from yggdrasil.communication.RMQComm import RMQComm
import yggdrasil.drivers.tests.test_ClientDriver as parent


_rmq_installed = RMQComm.is_installed(language='python')


@unittest.skipIf(not _rmq_installed, "RMQ Server not running")
@flaky.flaky
class TestRMQClientParam(parent.TestClientParam):
    r"""Test parameters for RMQClientDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestRMQClientParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQClientDriver'
        self.server_comm = 'RMQComm'
        self.ocomm_name = self.server_comm

    
@unittest.skipIf(not _rmq_installed, "RMQ Server not running")
@flaky.flaky
class TestRMQClientDriverNoStart(TestRMQClientParam,
                                 parent.TestClientDriverNoStart):
    r"""Test class for RMQClientDriver class without start."""
    pass


@unittest.skipIf(not _rmq_installed, "RMQ Server not running")
@flaky.flaky
class TestRMQClientDriver(TestRMQClientParam, parent.TestClientDriver):
    r"""Test class for RMQClientDriver class."""
    pass
