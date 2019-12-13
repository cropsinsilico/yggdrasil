import unittest
import copy
import flaky
from yggdrasil.tests import assert_raises
from yggdrasil.communication import new_comm
from yggdrasil.communication.RMQComm import RMQComm
from yggdrasil.communication.tests import test_RMQComm as parent


_rmq_installed = RMQComm.is_installed(language='python')


@unittest.skipIf(not _rmq_installed, "RMQ Server not running")
@flaky.flaky
class TestRMQAsyncComm(parent.TestRMQComm):
    r"""Test for RMQAsyncComm communication class."""

    comm = 'RMQAsyncComm'
    attr_list = (copy.deepcopy(parent.TestRMQComm.attr_list)
                 + ['times_connected', 'rmq_thread', 'rmq_lock'])

    def test_reconnect(self):
        r"""Test reconnect after unexpected disconnect."""
        self.recv_instance.connection.close(reply_code=100,
                                            reply_text="Test shutdown")
        T = self.recv_instance.start_timeout(5.0)
        while (not T.is_out) and (self.recv_instance.times_connected == 1):
            self.instance.sleep()
        self.instance.stop_timeout()

    # def test_send_recv_direct(self):
    #     r"""Disabled: Test send/recv direct."""
    #     pass
        

@unittest.skipIf(_rmq_installed, "RMQ Server running")
def test_not_running():
    r"""Test raise of an error if a RMQ server is not running."""
    comm_kwargs = dict(comm='RMQAsyncComm', direction='send', reverse_names=True)
    assert_raises(RuntimeError, new_comm, 'test', **comm_kwargs)
