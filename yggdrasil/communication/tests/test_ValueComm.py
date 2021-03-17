import copy
from yggdrasil.communication.tests import test_CommBase as parent


class TestValueComm(parent.TestCommBase):
    r"""Test for ValueComm communication class."""

    comm = 'ValueComm'
    attr_list = (copy.deepcopy(parent.TestCommBase.attr_list)
                 + ['remaining'])

    # Disable tests that don't make sense for ValueComm
    test_error_send = None
    test_error_recv = None
    test_work_comm = None
    test_drain_messages = None
    test_recv_nomsg = None
    test_send_recv_filter_eof = None
    test_send_recv_filter_pass = None
    test_send_recv_filter_send_filter = None
    test_send_recv_filter_recv_filter = None
    test_send_recv_nolimit = None
    test_send_recv_array = None
    test_eof = None
    test_eof_no_close = None
    test_send_recv_dict = None
    test_send_recv_dict_names = None

    @property
    def send_inst_kwargs(self):
        r"""dict: Keyword arguments for send instance."""
        out = super(TestValueComm, self).send_inst_kwargs
        out['direction'] = 'recv'
        return out
    
    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for tested class."""
        return self.send_inst_kwargs

    def test_send_recv(self):
        r"""Test send/recv of a small message."""
        n_recv = self.testing_options['kwargs']['count']
        msg_recv = self.test_msg
        if self.use_async:
            assert(self.recv_instance.n_msg_recv > 0)
        else:
            self.assert_equal(self.recv_instance.n_msg_recv, n_recv)
        # Wait for messages to be received
        for i in range(n_recv):
            flag, msg_recv0 = self.recv_instance.recv(self.timeout)
            assert(flag)
            self.assert_msg_equal(msg_recv0, msg_recv)
        # Receive after empty
        assert(self.recv_instance.is_open)
        flag, msg_recv0 = self.recv_instance.recv(self.timeout)
        assert(not flag)
        assert(self.recv_instance.is_eof(msg_recv0))
        # assert(flag)
        # assert(self.recv_instance.is_empty_recv(msg_recv0))
        # Confirm recept of messages
        self.recv_instance.wait_for_confirm(timeout=self.timeout)
        assert(self.recv_instance.is_confirmed)
        self.recv_instance.confirm(noblock=True)
        self.assert_equal(self.recv_instance.n_msg_recv, 0)

    def test_send_recv_after_close(self):
        r"""Test that opening twice dosn't cause errors and that send/recv after
        close returns false."""
        self.recv_instance.open()
        self.recv_instance.close()
        assert(self.recv_instance.is_closed)
        flag, msg_recv = self.recv_instance.recv()
        if not self.use_async:
            assert(not flag)
        self.assert_raises(RuntimeError, self.recv_instance.send, None)

    def test_purge(self, nrecv=1):
        r"""Test purging messages from the comm."""
        assert(self.recv_instance.n_msg > 0)
        self.recv_instance.purge()
        self.assert_equal(self.recv_instance.n_msg, 0)
        self.recv_instance.close()
        self.recv_instance.purge()
