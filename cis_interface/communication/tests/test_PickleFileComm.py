import nose.tools as nt
from cis_interface.communication.tests import test_FileComm as parent


class TestPickleFileComm(parent.TestFileComm):
    r"""Test for PickleFileComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestPickleFileComm, self).__init__(*args, **kwargs)
        self.comm = 'PickleFileComm'

    def test_send_recv(self):
        r"""Test send/recv of a small message."""
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)
        flag = self.send_instance.send(self.data_dict)
        assert(flag)
        nt.assert_equal(self.recv_instance.n_msg, 1)
        flag, msg_recv = self.recv_instance.recv()
        assert(flag)
        self.assert_equal_data_dict(msg_recv)
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)
        
    def test_send_recv_nolimit(self):
        r"""Test send/recv of a large message."""
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)
        flag = self.send_instance.send_nolimit(self.data_dict)
        assert(flag)
        assert(self.recv_instance.n_msg >= 1)
        flag, msg_recv = self.recv_instance.recv_nolimit()
        assert(flag)
        self.assert_equal_data_dict(msg_recv)
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)
