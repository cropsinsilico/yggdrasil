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
    
    def test_error_recv(self):
        r"""Disabled: Test error on recv."""
        pass
    
    def test_work_comm(self):
        r"""Disabled: Test creating/removing a work comm."""
        pass
    
    def test_eof(self):
        r"""Test send/recv of EOF message."""
        # Forwards
        self.do_send_recv(send_meth='send_eof')
        # Backwards
        self.do_send_recv(send_meth='send_eof', reverse_comms=True)

    def test_eof_no_close(self):
        r"""Test send/recv of EOF message with no close."""
        # Forwards
        self.recv_instance.icomm.close_on_eof_recv = False
        self.do_send_recv(send_meth='send_eof', close_on_recv_eof=False)
        # Backwards
        self.send_instance.icomm.close_on_eof_recv = False
        self.do_send_recv(send_meth='send_eof', close_on_recv_eof=False,
                          reverse_comms=True)

    def test_eof_nolimit(self):
        r"""Test send/recv of EOF message through nolimit."""
        # Forwards
        self.do_send_recv(send_meth='send_nolimit_eof')
        # Backwards
        self.do_send_recv(send_meth='send_nolimit_eof', reverse_comms=True)

    def test_call(self):
        r"""Test RPC call."""
        self.send_instance.sched_task(0.01, self.send_instance.send,
                                      args=[self.msg_short])
        flag, msg_recv = self.recv_instance.call(self.msg_short,
                                                 timeout=self.timeout)
        assert(flag)
        nt.assert_equal(msg_recv, self.msg_short)
        flag, msg_recv = self.send_instance.recv(timeout=self.timeout)
        assert(flag)
        nt.assert_equal(msg_recv, self.msg_short)
        self.recv_instance.close()
        flag, msg_recv = self.recv_instance.call(self.msg_short)
        assert(not flag)

    def test_call_alias(self):
        r"""Test RPC call aliases."""
        self.send_instance.sched_task(0.01, self.send_instance.rpcSend,
                                      args=[self.msg_short])
        flag, msg_recv = self.recv_instance.rpcCall(self.msg_short,
                                                    timeout=self.timeout)
        nt.assert_equal(msg_recv, self.msg_short)
        flag, msg_recv = self.send_instance.rpcRecv(timeout=self.timeout)
        nt.assert_equal(msg_recv, self.msg_short)

    def test_call_nolimit(self):
        r"""Test RPC nolimit call."""
        self.send_instance.sched_task(0.01, self.send_instance.send_nolimit,
                                      args=[self.msg_long])
        flag, msg_recv = self.recv_instance.call_nolimit(self.msg_long,
                                                         timeout=self.timeout)
        nt.assert_equal(msg_recv, self.msg_long)
        flag, msg_recv = self.send_instance.recv_nolimit(timeout=self.timeout)
        nt.assert_equal(msg_recv, self.msg_long)
