import nose.tools as nt
from cis_interface.communication.tests import test_AsciiFileComm as parent


class TestAsciiTableComm(parent.TestAsciiFileComm):
    r"""Test for AsciiTableComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestAsciiTableComm, self).__init__(*args, **kwargs)
        self.comm = 'AsciiTableComm'
        self.attr_list += ['as_array']

    @property
    def send_inst_kwargs(self):
        r"""dict: Keyword arguments for send instance."""
        out = super(TestAsciiTableComm, self).send_inst_kwargs
        out['format_str'] = self.fmt_str
        return out

    def test_send_recv(self):
        r"""Test send/recv of a table line."""
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)
        flag = self.send_instance.send(self.file_lines[0])
        assert(flag)
        nt.assert_equal(self.recv_instance.n_msg, 1)
        flag, msg_recv = self.recv_instance.recv()
        assert(flag)
        nt.assert_equal(msg_recv, self.file_lines[0])
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)

    def test_send_recv_nolimit(self):
        r"""Test send/recv of a table line as a large message."""
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)
        flag = self.send_instance.send_nolimit(self.file_lines[0])
        assert(flag)
        assert(self.recv_instance.n_msg >= 1)
        # IPC nolimit sends multiple messages
        # nt.assert_equal(self.recv_instance.n_msg, 1)
        flag, msg_recv = self.recv_instance.recv_nolimit()
        assert(flag)
        nt.assert_equal(msg_recv, self.file_lines[0])
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)


class TestAsciiTableComm_AsArray(TestAsciiTableComm):
    r"""Test for AsciiTableComm communication class."""

    @property
    def send_inst_kwargs(self):
        r"""dict: Keyword arguments for send instance."""
        out = super(TestAsciiTableComm_AsArray, self).send_inst_kwargs
        out['as_array'] = True
        return out

    def test_send_recv(self):
        r"""Test send/recv of a table array."""
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)
        flag = self.send_instance.send(self.file_bytes)
        assert(flag)
        nt.assert_equal(self.recv_instance.n_msg, 1)
        flag, msg_recv = self.recv_instance.recv()
        assert(flag)
        nt.assert_equal(msg_recv, self.file_bytes)
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)

    def test_send_recv_nolimit(self):
        r"""Test send/recv of a table array as a large message."""
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)
        flag = self.send_instance.send_nolimit(self.file_bytes)
        assert(flag)
        assert(self.recv_instance.n_msg >= 1)
        # IPC nolimit sends multiple messages
        # nt.assert_equal(self.recv_instance.n_msg, 1)
        flag, msg_recv = self.recv_instance.recv_nolimit()
        assert(flag)
        nt.assert_equal(msg_recv, self.file_bytes)
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)
