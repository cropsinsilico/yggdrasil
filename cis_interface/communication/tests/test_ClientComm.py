import nose.tools as nt
from cis_interface.communication.tests import test_CommBase


class TestClientComm(test_CommBase.TestCommBase):
    r"""Tests for ClientComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestClientComm, self).__init__(*args, **kwargs)
        self.comm = 'ServerComm'
        self.attr_list += ['response_kwargs', 'icomm', 'ocomm']

    @property
    def send_inst_kwargs(self):
        r"""dict: Keyword arguments for send instance."""
        return {'comm': 'ClientComm'}
    
    def test_eof(self):
        r"""Test send/recv of EOF message."""
        # Forwards
        flag = self.send_instance.send_eof()
        assert(flag)
        flag, msg_recv = self.recv_instance.recv()
        assert(not flag)
        nt.assert_equal(msg_recv, self.send_instance.eof_msg)
        # Assert
        # assert(self.recv_instance.is_closed)

    def test_eof_nolimit(self):
        r"""Test send/recv of EOF message through nolimit."""
        # Forwards
        flag = self.send_instance.send_nolimit_eof()
        assert(flag)
        flag, msg_recv = self.recv_instance.recv_nolimit()
        assert(not flag)
        nt.assert_equal(msg_recv, self.send_instance.eof_msg)
        # Assert
        # assert(self.recv_instance.is_closed)

    def test_call(self):
        r"""Test RPC call."""
        self.send_instance.sched_task(0.0, self.send_instance.call,
                                      args=[self.msg_short], store_output=True)
        flag, msg_recv = self.recv_instance.recv(timeout=self.timeout)
        
        assert(flag)
        nt.assert_equal(msg_recv, self.msg_short)
        flag = self.recv_instance.send(msg_recv)
        assert(flag)
        T = self.recv_instance.start_timeout()
        while (not T.is_out) and (self.send_instance.sched_out is None):
            self.recv_instance.sleep()
        self.recv_instance.stop_timeout()
        flag, msg_recv = self.send_instance.sched_out
        assert(flag)
        nt.assert_equal(msg_recv, self.msg_short)

    def test_call_nolimit(self):
        r"""Test RPC nolimit call."""
        self.send_instance.sched_task(0.0, self.send_instance.call_nolimit,
                                      args=[self.msg_long], store_output=True)
        flag, msg_recv = self.recv_instance.recv_nolimit(timeout=self.timeout)
        assert(flag)
        nt.assert_equal(msg_recv, self.msg_long)
        flag = self.recv_instance.send_nolimit(msg_recv)
        assert(flag)
        T = self.recv_instance.start_timeout()
        while (not T.is_out) and (self.send_instance.sched_out is None):
            self.recv_instance.sleep()
        self.recv_instance.stop_timeout()
        flag, msg_recv = self.send_instance.sched_out
        assert(flag)
        nt.assert_equal(msg_recv, self.msg_long)
