import copy
from yggdrasil.communication.tests import test_FileComm as parent


class TestAsciiFileComm(parent.TestFileComm):
    r"""Test for AsciiFileComm communication class."""

    comm = 'AsciiFileComm'
    attr_list = (copy.deepcopy(parent.TestFileComm.attr_list)
                 + ['comment'])

    def test_send_recv_comment(self):
        r"""Test send/recv with commented message."""
        msg_send = self.send_instance.serializer.comment + self.test_msg
        flag = self.send_instance.send(msg_send)
        assert(flag)
        flag, msg_recv = self.recv_instance.recv()
        assert(not flag)
        self.assert_equal(msg_recv, self.recv_instance.eof_msg)
