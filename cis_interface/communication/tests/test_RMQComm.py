import unittest
import nose.tools as nt
from cis_interface.communication import new_comm
from cis_interface.communication.RMQComm import _rmq_server_running
from cis_interface.communication.tests import test_AsyncComm


@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQComm(test_AsyncComm.TestAsyncComm):
    r"""Test for RMQComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestRMQComm, self).__init__(*args, **kwargs)
        self.comm = 'RMQComm'
        self.attr_list += ['connection', 'channel']
        self.timeout = 10.0

    def test_double_open(self):
        r"""test that opening/binding twice dosn't cause errors."""
        super(TestRMQComm, self).test_double_open()
        self.send_instance.bind()
        self.recv_instance.bind()


@unittest.skipIf(_rmq_server_running, "RMQ Server running")
def test_not_running():
    r"""Test raise of an error if a RMQ server is not running."""
    comm_kwargs = dict(comm='RMQComm', direction='send', reverse_names=True)
    nt.assert_raises(RuntimeError, new_comm, 'test', **comm_kwargs)
