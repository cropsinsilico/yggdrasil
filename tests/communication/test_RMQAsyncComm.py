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

    def test_reconnect_recv(self):
        r"""Test reconnect after unexpected disconnect of recv comm."""
        self.do_send_recv(print_status=True)
        self.recv_instance.connection.close(reply_code=100,
                                            reply_text="Test shutdown")
        self.recv_instance._reconnecting.started.wait(5)
        self.recv_instance._reconnecting.stopped.wait(5)
        assert(self.recv_instance.times_connected > 1)
        assert(self.recv_instance._reconnecting.has_stopped())
        self.do_send_recv(print_status=True)


class TestRMQAsyncCommNamedQueue(TestRMQAsyncComm):
    r"""Test for RMQAsyncComm communication class with a named queue."""

    test_attributes = None
    test_cleanup_comms = None
    test_drain_messages = None
    test_empty_obj_recv = None
    test_eof = None
    test_eof_no_close = None
    test_error_name = None
    test_error_recv = None
    test_error_send = None
    test_invalid_direction = None
    test_purge = None
    test_recv_nomsg = None
    test_send_recv = None
    test_send_recv_after_close = None
    test_send_recv_array = None
    test_send_recv_dict = None
    test_send_recv_dict_names = None
    test_send_recv_filter_eof = None
    test_send_recv_filter_pass = None
    test_send_recv_filter_recv_filter = None
    test_send_recv_filter_send_filter = None
    test_send_recv_nolimit = None
    test_send_recv_raw = None
    test_work_comm = None

    @property
    def send_inst_kwargs(self):
        r"""dict: Keyword arguments for send instance."""
        out = super(TestRMQAsyncCommNamedQueue, self).send_inst_kwargs
        out['queue'] = 'test_queue'
        return out
    
    def test_reconnect_send(self):
        r"""Test reconnect after unexpected disconnect of send comm."""
        self.send_instance.start_run_thread()
        self.do_send_recv(print_status=True)
        self.send_instance.connection.close(reply_code=100,
                                            reply_text="Test shutdown")
        self.send_instance._reconnecting.started.wait(5)
        self.send_instance._reconnecting.stopped.wait(10)
        assert(self.send_instance.times_connected > 1)
        assert(self.send_instance._reconnecting.has_stopped())
        self.do_send_recv(print_status=True)
        

@unittest.skipIf(_rmq_installed, "RMQ Server running")
def test_not_running():
    r"""Test raise of an error if a RMQ server is not running."""
    comm_kwargs = dict(commtype='rmq_async', direction='send', reverse_names=True)
    assert_raises(RuntimeError, new_comm, 'test', **comm_kwargs)
