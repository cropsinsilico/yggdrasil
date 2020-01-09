import unittest
import flaky
from yggdrasil.communication.RMQComm import RMQComm
import yggdrasil.drivers.tests.test_ServerDriver as parent


_rmq_installed = RMQComm.is_installed(language='python')


@unittest.skipIf(not _rmq_installed, "RMQ Server not running")
@flaky.flaky
class TestRMQServerParam(parent.TestServerParam):
    r"""Test parameters for RMQServerDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestRMQServerParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQServerDriver'
        self.client_comm = 'RMQComm'
        self.icomm_name = self.client_comm

    
@unittest.skipIf(not _rmq_installed, "RMQ Server not running")
@flaky.flaky
class TestRMQServerDriverNoStart(TestRMQServerParam,
                                 parent.TestServerDriverNoStart):
    r"""Test class for RMQServerDriver class without start."""
    pass


@unittest.skipIf(not _rmq_installed, "RMQ Server not running")
@flaky.flaky
class TestRMQServerDriver(TestRMQServerParam, parent.TestServerDriver):
    r"""Test class for RMQServerDriver class."""
    pass
