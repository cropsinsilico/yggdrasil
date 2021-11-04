import pytest
import flaky
from tests.communication.test_CommBase import TestComm as base_class
from yggdrasil.communication import new_comm
from yggdrasil.communication.RMQComm import RMQComm
from tests import timeout_decorator


@flaky.flaky
@timeout_decorator(timeout=60)
class TestRMQAsyncComm(base_class):
    r"""Test for RMQAsyncComm communication class."""

    @pytest.fixture(scope="class", autouse=True)
    def commtype(self):
        r"""Communicator type being tested."""
        return "rmq_async"

    @pytest.fixture(autouse=True)
    def ensure_comm(self, send_comm, recv_comm):
        pass

    def test_reconnect_recv(self, send_comm, recv_comm, do_send_recv):
        r"""Test reconnect after unexpected disconnect of recv comm."""
        send_comm.printStatus()
        recv_comm.printStatus()
        do_send_recv(send_comm, recv_comm)
        recv_comm.connection.close(reply_code=100,
                                   reply_text="Test shutdown")
        recv_comm._reconnecting.started.wait(5)
        recv_comm._reconnecting.stopped.wait(5)
        assert(recv_comm.times_connected > 1)
        assert(recv_comm._reconnecting.has_stopped())
        recv_comm._opening.stopped.wait(5)
        do_send_recv(send_comm, recv_comm)
        send_comm.printStatus()
        recv_comm.printStatus()


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

    @pytest.fixture(scope="class")
    def testing_options(self, python_class, options):
        r"""Testing options."""
        out = python_class.get_testing_options(**options)
        out['kwargs'].update(queue='test_queue')
        return out
    
    def test_reconnect_send(self, send_comm, recv_comm, do_send_recv):
        r"""Test reconnect after unexpected disconnect of send comm."""
        send_comm.start_run_thread()
        send_comm.printStatus()
        recv_comm.printStatus()
        do_send_recv(send_comm, recv_comm)
        send_comm.connection.close(reply_code=100,
                                   reply_text="Test shutdown")
        send_comm._reconnecting.started.wait(5)
        send_comm._reconnecting.stopped.wait(10)
        assert(send_comm.times_connected > 1)
        assert(send_comm._reconnecting.has_stopped())
        do_send_recv(send_comm, recv_comm)
        send_comm.printStatus()
        recv_comm.printStatus()


@pytest.mark.skipif(RMQComm.is_installed(language='python'),
                    reason="RMQ Server running")
def test_not_running():
    r"""Test raise of an error if a RMQ server is not running."""
    comm_kwargs = dict(commtype='rmq_async', direction='send',
                       reverse_names=True)
    with pytest.raises(RuntimeError):
        new_comm('test', **comm_kwargs)
