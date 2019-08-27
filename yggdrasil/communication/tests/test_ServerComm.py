import unittest
import uuid
import copy
from yggdrasil.communication import new_comm
from yggdrasil.communication.tests import test_CommBase


class TestServerComm(test_CommBase.TestCommBase):
    r"""Tests for ServerComm communication class."""

    comm = 'ServerComm'
    attr_list = (copy.deepcopy(test_CommBase.TestCommBase.attr_list)
                 + ['response_kwargs', 'icomm', 'ocomm'])

    @property
    def send_inst_kwargs(self):
        r"""dict: Keyword arguments for send instance."""
        return {'comm': 'ClientComm'}
    
    @unittest.skipIf(True, 'Server')
    def test_error_send(self):
        r"""Disabled: Test error on send."""
        pass  # pragma: no cover
        
    @unittest.skipIf(True, 'Server')
    def test_error_recv(self):
        r"""Disabled: Test error on recv."""
        pass  # pragma: no cover
        
    @unittest.skipIf(True, 'Server')
    def test_invalid_direction(self):
        r"""Disabled: Test of error on incorrect direction."""
        pass  # pragma: no cover
    
    @unittest.skipIf(True, 'Server')
    def test_work_comm(self):
        r"""Disabled: Test creating/removing a work comm."""
        pass  # pragma: no cover

    def test_newcomm_server(self):
        r"""Test creation of server using newcomm."""
        inst = new_comm('testserver_%s' % str(uuid.uuid4()), comm=self.comm)
        self.remove_instance(inst)
        
    def test_eof_no_close(self):
        r"""Test send/recv of EOF message with no close."""
        # Forwards
        self.recv_instance.icomm.close_on_eof_recv = False
        self.do_send_recv(send_meth='send_eof', close_on_recv_eof=False)

    def test_call(self):
        r"""Test RPC call."""
        self.send_instance.sched_task(0.0, self.send_instance.rpcCall,
                                      args=[self.test_msg], store_output=True)
        flag, msg_recv = self.recv_instance.rpcRecv(timeout=self.timeout)
        assert(flag)
        self.assert_equal(msg_recv, self.test_msg)
        flag = self.recv_instance.rpcSend(msg_recv)
        assert(flag)
        T = self.recv_instance.start_timeout()
        while (not T.is_out) and (self.send_instance.sched_out is None):  # pragma: debug
            self.recv_instance.sleep()
        self.recv_instance.stop_timeout()
        flag, msg_recv = self.send_instance.sched_out
        assert(flag)
        self.assert_equal(msg_recv, self.test_msg)

    def test_call_alias(self):
        r"""Test RPC call aliases."""
        # self.send_instance.sched_task(0.0, self.send_instance.rpcSend,
        #                               args=[self.test_msg], store_output=True)
        self.recv_instance.sched_task(self.sleeptime, self.recv_instance.rpcRecv,
                                      kwargs=dict(timeout=self.timeout),
                                      store_output=True)
        flag = self.send_instance.rpcSend(self.test_msg)
        assert(flag)
        T = self.recv_instance.start_timeout()
        while (not T.is_out) and (self.recv_instance.sched_out is None):  # pragma: debug
            self.recv_instance.sleep()
        self.recv_instance.stop_timeout()
        flag, msg_recv = self.recv_instance.sched_out
        # flag, msg_recv = self.recv_instance.rpcRecv(timeout=self.timeout)
        assert(flag)
        self.assert_equal(msg_recv, self.test_msg)
        flag = self.recv_instance.rpcSend(msg_recv)
        assert(flag)
        flag, msg_recv = self.send_instance.rpcRecv(timeout=self.timeout)
        assert(flag)
        self.assert_equal(msg_recv, self.test_msg)

    def test_call_nolimit(self):
        r"""Test RPC nolimit call."""
        self.send_instance.sched_task(0.0, self.send_instance.call_nolimit,
                                      args=[self.msg_long], store_output=True)
        flag, msg_recv = self.recv_instance.recv_nolimit(timeout=self.timeout)
        assert(flag)
        self.assert_equal(msg_recv, self.msg_long)
        flag = self.recv_instance.send_nolimit(msg_recv)
        assert(flag)
        T = self.recv_instance.start_timeout()
        while (not T.is_out) and (self.send_instance.sched_out is None):  # pragma: debug
            self.recv_instance.sleep()
        self.recv_instance.stop_timeout()
        flag, msg_recv = self.send_instance.sched_out
        assert(flag)
        self.assert_equal(msg_recv, self.msg_long)

    def test_close_in_thread(self):
        r"""Test close of comm in thread."""
        self.send_instance.close_in_thread()
        self.recv_instance.close_in_thread()

    def add_filter(self, comm, filter=None):
        r"""Add a filter to a comm.

        Args:
            comm (CommBase): Communication instance to add a filter to.
            filter (FilterBase, optional): Filter class. Defaults to None and is ignored.

        """
        target = comm
        if comm.comm_class == 'ServerComm':
            target = comm.icomm
        elif comm.comm_class == 'ClientComm':
            target = comm.ocomm
        return super(TestServerComm, self).add_filter(target, filter=filter)
        
    # # This dosn't work for comms that are uni-directional
    # def test_purge_recv(self):
    #     r"""Test purging messages from the client comm."""
    #     # Purge send while open
    #     if self.comm != 'CommBase':
    #         flag = self.send_instance.send(self.test_msg)
    #         assert(flag)
    #         T = self.recv_instance.start_timeout()
    #         while (not T.is_out) and (self.recv_instance.n_msg == 0):  # pragma: debug
    #             self.recv_instance.sleep()
    #         self.recv_instance.stop_timeout()
    #         self.assert_equal(self.recv_instance.n_msg, 1)
    #     self.send_instance.purge()
    #     self.assert_equal(self.send_instance.n_msg, 0)
    #     self.assert_equal(self.recv_instance.n_msg, 0)
    #     # Purge send while closed
    #     self.send_instance.close()
    #     self.send_instance.purge()
