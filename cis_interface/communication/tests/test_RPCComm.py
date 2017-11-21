import nose.tools as nt
from cis_interface.communication.tests import test_CommBase


class TestRPCComm(test_CommBase.TestCommBase):
    r"""Tests for RPCComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestRPCComm, self).__init__(*args, **kwargs)
        self.comm = 'RPCComm'
        self.attr_list += ['icomm', 'ocomm']

    def test_error_send(self):
        r"""Disabled: Test error on send."""
        pass
    
    def test_work_comm(self):
        r"""Disabled: Test creating/removing a work comm."""
        pass
    
    def test_eof(self):
        r"""Test send/recv of EOF message."""
        # Forwards
        flag = self.send_instance.send(self.send_instance.eof_msg)
        assert(flag)
        flag, msg_recv = self.recv_instance.recv()
        assert(not flag)
        nt.assert_equal(msg_recv, self.send_instance.eof_msg)
        # Backwards
        flag = self.recv_instance.send(self.recv_instance.eof_msg)
        assert(flag)
        flag, msg_recv = self.send_instance.recv()
        assert(not flag)
        nt.assert_equal(msg_recv, self.recv_instance.eof_msg)
        # Assert
        # assert(self.recv_instance.is_closed)

    def test_eof_nolimit(self):
        r"""Test send/recv of EOF message through nolimit."""
        # Forwards
        flag = self.send_instance.send_nolimit(self.send_instance.eof_msg)
        assert(flag)
        flag, msg_recv = self.recv_instance.recv_nolimit()
        assert(not flag)
        nt.assert_equal(msg_recv, self.send_instance.eof_msg)
        # Backwards
        flag = self.recv_instance.send_nolimit(self.recv_instance.eof_msg)
        assert(flag)
        flag, msg_recv = self.send_instance.recv_nolimit()
        assert(not flag)
        nt.assert_equal(msg_recv, self.recv_instance.eof_msg)
        # Assert
        # assert(self.recv_instance.is_closed)

    def test_call(self):
        r"""Test RPC call."""
        self.send_instance.sched_task(0.01, self.send_instance.send,
                                      args=[self.msg_short])
        flag, msg_recv = self.recv_instance.call(self.msg_short)
        nt.assert_equal(msg_recv, self.msg_short)
        flag, msg_recv = self.send_instance.recv()
        nt.assert_equal(msg_recv, self.msg_short)
        self.recv_instance.close()
        flag, msg_recv = self.recv_instance.call(self.msg_short)
        assert(not flag)

    def test_call_alias(self):
        r"""Test RPC call aliases."""
        self.send_instance.sched_task(0.01, self.send_instance.rpcSend,
                                      args=[self.msg_short])
        flag, msg_recv = self.recv_instance.rpcCall(self.msg_short)
        nt.assert_equal(msg_recv, self.msg_short)
        flag, msg_recv = self.send_instance.rpcRecv()
        nt.assert_equal(msg_recv, self.msg_short)

    def test_call_nolimit(self):
        r"""Test RPC nolimit call."""
        self.send_instance.sched_task(0.01, self.send_instance.send_nolimit,
                                      args=[self.msg_long])
        flag, msg_recv = self.recv_instance.call_nolimit(self.msg_long)
        nt.assert_equal(msg_recv, self.msg_long)
        flag, msg_recv = self.send_instance.recv_nolimit()
        nt.assert_equal(msg_recv, self.msg_long)
