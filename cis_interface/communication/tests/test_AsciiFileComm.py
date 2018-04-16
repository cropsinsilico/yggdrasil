import nose.tools as nt
from cis_interface.communication.tests import test_FileComm as parent


class TestAsciiFileComm(parent.TestFileComm):
    r"""Test for AsciiFileComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestAsciiFileComm, self).__init__(*args, **kwargs)
        self.comm = 'AsciiFileComm'
        self.attr_list += ['comment']

    def test_send_recv_comment(self):
        r"""Test send/recv with commented message."""
        msg_send = self.send_instance.comment + self.test_msg
        flag = self.send_instance.send(msg_send)
        assert(flag)
        flag, msg_recv = self.recv_instance.recv()
        assert(not flag)
        nt.assert_equal(msg_recv, self.recv_instance.eof_msg)
