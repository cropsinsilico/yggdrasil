import unittest
import flaky
from yggdrasil.communication.RMQComm import RMQComm
import yggdrasil.drivers.tests.test_ClientDriver as parent


_rmq_installed = RMQComm.is_installed(language='python')


@unittest.skipIf(not _rmq_installed, "RMQ Server not running")
@flaky.flaky
class TestRMQAsyncClientParam(parent.TestClientParam):
    r"""Test parameters for RMQAsyncClientDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestRMQAsyncClientParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQAsyncClientDriver'
        self.server_comm = 'RMQAsyncComm'
        self.ocomm_name = self.server_comm
        self.timeout = 10.0
        self.route_timeout = 60.0


@unittest.skipIf(not _rmq_installed, "RMQ Server not running")
@flaky.flaky
class TestRMQAsyncClientDriverNoStart(TestRMQAsyncClientParam,
                                      parent.TestClientDriverNoStart):
    r"""Test class for RMQAsyncClientDriver class without start."""
    pass


@unittest.skipIf(not _rmq_installed, "RMQ Server not running")
@flaky.flaky
class TestRMQAsyncClientDriver(TestRMQAsyncClientParam, parent.TestClientDriver):
    r"""Test class for RMQAsyncClientDriver class."""
    pass
