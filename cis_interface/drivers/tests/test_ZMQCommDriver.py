import unittest
from cis_interface.tools import _zmq_installed
from cis_interface.drivers.tests import test_CommDriver as parent


@unittest.skipIf(not _zmq_installed, "ZMQ library not installed")
class TestZMQCommParam(parent.TestCommParam):
    r"""Test parameters for the ZMQCommDriver class."""
    def __init__(self, *args, **kwargs):
        super(TestZMQCommParam, self).__init__(*args, **kwargs)
        self.driver = 'ZMQCommDriver'
        self.comm_name = 'ZMQComm'
        self._cleanup_comm_class = self.comm_name
    

@unittest.skipIf(not _zmq_installed, "ZMQ library not installed")
class TestZMQCommDriverNoStart(TestZMQCommParam, parent.TestCommDriverNoStart):
    r"""Test class for the ZMQCommDriver class without start."""
    pass


@unittest.skipIf(not _zmq_installed, "ZMQ library not installed")
class TestZMQCommDriver(TestZMQCommParam, parent.TestCommDriver):
    r"""Test class for the ZMQCommDriver class."""
    pass
