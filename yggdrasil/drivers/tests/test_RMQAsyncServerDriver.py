import unittest
import flaky
from yggdrasil.communication.RMQComm import RMQComm
import yggdrasil.drivers.tests.test_ServerDriver as parent


_rmq_installed = RMQComm.is_installed(language='python')


@unittest.skipIf(not _rmq_installed, "RMQ Server not running")
@flaky.flaky
class TestRMQAsyncServerParam(parent.TestServerParam):
    r"""Test parameters for RMQAsyncServerDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestRMQAsyncServerParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQAsyncServerDriver'
        self.client_comm = 'RMQAsyncComm'
        self.icomm_name = self.client_comm
        self.timeout = 10.0
        self.route_timeout = 60.0


@unittest.skipIf(not _rmq_installed, "RMQ Server not running")
@flaky.flaky
class TestRMQAsyncServerDriverNoStart(TestRMQAsyncServerParam,
                                      parent.TestServerDriverNoStart):
    r"""Test class for RMQAsyncServerDriver class without start."""
    pass


@unittest.skipIf(not _rmq_installed, "RMQ Server not running")
@flaky.flaky
class TestRMQAsyncServerDriver(TestRMQAsyncServerParam, parent.TestServerDriver):
    r"""Test class for RMQAsyncServerDriver class."""
    pass
