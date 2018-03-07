import nose.tools as nt
from cis_interface.communication.tests import test_CommBase


class TestAsyncComm(test_CommBase.TestCommBase):
    r"""Tests for AsyncComm communication class."""

    def __init__(self, *args, **kwargs):
        super(TestAsyncComm, self).__init__(*args, **kwargs)
        self.comm = 'AsyncComm'
        self.attr_list += ['dont_backlog', 'backlog_send_ready',
                           'backlog_recv_ready']

    def test_send_recv_after_close(self):
        r"""Test that send/recv after close returns false."""
        super(TestAsyncComm, self).test_send_recv_after_close()
        nt.assert_equal(self.send_instance.n_msg_direct_send, 0)
        nt.assert_equal(self.recv_instance.n_msg_direct_recv, 0)

    def test_send_recv_direct(self):
        r"""Test send/recv direct."""
        self.send_instance.n_msg_backlog
        self.recv_instance.n_msg_backlog
        self.send_instance.backlog_thread.set_break_flag()
        self.recv_instance.backlog_thread.set_break_flag()
        self.send_instance.dont_backlog = True
        self.recv_instance.dont_backlog = True
        self.do_send_recv(send_kwargs={'no_backlog': True, 'no_confirm': True},
                          recv_kwargs={'no_backlog': True, 'no_confirm': True})
