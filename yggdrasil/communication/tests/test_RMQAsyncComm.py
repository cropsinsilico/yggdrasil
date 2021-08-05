import unittest
import copy
import flaky
from yggdrasil.tests import assert_raises, timeout
from yggdrasil.communication import new_comm
from yggdrasil.communication.RMQComm import RMQComm
from yggdrasil.communication.tests import test_RMQComm as parent


_rmq_installed = RMQComm.is_installed(language='python')


@unittest.skipIf(not _rmq_installed, "RMQ Server not running")
@flaky.flaky
@timeout(timeout=60)
class TestRMQAsyncComm(parent.TestRMQComm):
    r"""Test for RMQAsyncComm communication class."""

    comm = 'RMQAsyncComm'
    attr_list = (copy.deepcopy(parent.TestRMQComm.attr_list)
                 + ['times_connected', 'rmq_thread', 'rmq_lock'])

    def test_reconnect(self):
        r"""Test reconnect after unexpected disconnect."""
        self.recv_instance.connection.close(reply_code=100,
                                            reply_text="Test shutdown")
        self.recv_instance._reconnecting.started.wait(5)
        self.recv_instance._reconnecting.stopped.wait(5)
        assert(self.recv_instance.times_connected > 1)
        assert(self.recv_instance._reconnecting.has_stopped())
        self.do_send_recv(print_status=True)
        

@unittest.skipIf(_rmq_installed, "RMQ Server running")
def test_not_running():
    r"""Test raise of an error if a RMQ server is not running."""
    comm_kwargs = dict(commtype='rmq_async', direction='send', reverse_names=True)
    assert_raises(RuntimeError, new_comm, 'test', **comm_kwargs)
