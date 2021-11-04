import pytest
import uuid
from yggdrasil.communication import new_comm
from tests.communication.test_CommBase import TestComm as base_class


class TestServerComm(base_class):
    r"""Tests for ServerComm communication class."""

    test_error_send = None
    test_error_recv = None
    test_invalid_direction = None
    test_work_comm = None
    test_send_recv_raw = None

    @pytest.fixture(scope="class", autouse=True)
    def commtype(self):
        r"""Communicator type being tested."""
        return "server"

    @pytest.fixture(scope="class", autouse=True)
    def python_class(self):
        r"""Python class that is being tested."""
        from yggdrasil.communication.ServerComm import ServerComm
        return ServerComm

    def get_send_comm_kwargs(self, commtype, send_comm,
                             testing_options, **kwargs):
        r"""Get keyword arguments for creating a send comm."""
        kwargs.update(direct_connection=True)
        out = super(TestServerComm, self).get_send_comm_kwargs(
            'client', send_comm, testing_options, **kwargs)
        return out

    def test_newcomm_server(self, commtype, close_comm):
        r"""Test creation of server using newcomm."""
        inst = new_comm('testserver_%s' % str(uuid.uuid4()),
                        commtype=commtype)
        close_comm(inst)
        
    def test_call(self, send_comm, recv_comm, testing_options, timeout,
                  wait_on_function):
        r"""Test RPC call."""
        send_comm.maxMsgSize
        recv_comm.maxMsgSize
        send_comm.opp_comms
        recv_comm.opp_comms
        send_comm.sched_task(0.0, send_comm.rpcCall,
                             args=[testing_options['msg']],
                             store_output=True)
        flag, msg_recv = recv_comm.rpcRecv(timeout=timeout)
        assert(flag)
        assert(msg_recv == testing_options['msg'])
        flag = recv_comm.rpcSend(msg_recv)
        assert(flag)
        wait_on_function(lambda: (send_comm.sched_out is not None))
        flag, msg_recv = send_comm.sched_out
        assert(flag)
        assert(msg_recv == testing_options['msg'])

    def test_call_alias(self, send_comm, recv_comm, testing_options,
                        timeout, polling_interval, wait_on_function):
        r"""Test RPC call aliases."""
        # send_comm.sched_task(0.0, send_comm.rpcSend,
        #                      args=[testing_options['msg']],
        #                      store_output=True)
        recv_comm.sched_task(polling_interval, recv_comm.rpcRecv,
                             kwargs=dict(timeout=timeout),
                             store_output=True)
        flag = send_comm.rpcSend(testing_options['msg'])
        assert(flag)
        wait_on_function(lambda: (recv_comm.sched_out is not None))
        flag, msg_recv = recv_comm.sched_out
        # flag, msg_recv = recv_comm.rpcRecv(timeout=timeout)
        assert(flag)
        assert(msg_recv == testing_options['msg'])
        flag = recv_comm.rpcSend(msg_recv)
        assert(flag)
        flag, msg_recv = send_comm.rpcRecv(timeout=timeout)
        assert(flag)
        assert(msg_recv == testing_options['msg'])

    def test_call_nolimit(self, send_comm, recv_comm, msg_long, timeout,
                          wait_on_function):
        r"""Test RPC nolimit call."""
        send_comm.sched_task(0.0, send_comm.call_nolimit,
                             args=[msg_long], store_output=True)
        msg = recv_comm.recv_nolimit(timeout=timeout,
                                     return_message_object=True)
        flag = bool(msg.flag)
        msg_recv = msg.args
        header = msg.header
        assert(flag)
        assert(msg_recv == msg_long)
        assert(isinstance(header, dict))
        flag = recv_comm.send_nolimit(msg_recv)
        assert(flag)
        T = recv_comm.start_timeout()
        while (not T.is_out) and (send_comm.sched_out is None):  # pragma: debug
            recv_comm.sleep()
        recv_comm.stop_timeout()
        flag, msg_recv = send_comm.sched_out
        assert(flag)
        assert(msg_recv == msg_long)

    def test_close_in_thread(self, send_comm, recv_comm):
        r"""Test close of comm in thread."""
        send_comm.close_in_thread()
        recv_comm.close_in_thread()

    def add_filter(self, comm, filter=None, **kwargs):
        r"""Add a filter to a comm.

        Args:
            comm (CommBase): Communication instance to add a filter to.
            filter (FilterBase, optional): Filter class. Defaults to None and is ignored.

        """
        target = comm
        if comm._commtype == 'server':
            target = comm.icomm
        elif comm._commtype == 'client':
            target = comm.ocomm
        return super(TestServerComm, self).add_filter(target, filter=filter,
                                                      **kwargs)
        
    # # This dosn't work for comms that are uni-directional
    # def test_purge_recv(self, send_comm, recv_comm, testing_options,
    #                     wait_on_function):
    #     r"""Test purging messages from the client comm."""
    #     # Purge send while open
    #     flag = send_comm.send(testing_options['msg'])
    #     assert(flag)
    #     wait_on_function(lambda: (recv_comm.n_msg != 0))
    #     assert(recv_comm.n_msg == 1)
    #     send_comm.purge()
    #     assert(send_comm.n_msg == 0)
    #     assert(recv_comm.n_msg == 0)
    #     # Purge send while closed
    #     send_comm.close()
    #     send_comm.purge()
