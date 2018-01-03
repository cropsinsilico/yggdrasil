import nose.tools as nt
from cis_interface.communication import new_comm
from cis_interface.communication.tests import test_CommBase as parent


class TestFileComm(parent.TestCommBase):
    r"""Test for FileComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestFileComm, self).__init__(*args, **kwargs)
        self.comm = 'FileComm'
        self.attr_list += ['fd', 'read_meth', 'append']
        self.read_meth = 'read'

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for tested class."""
        out = super(TestFileComm, self).inst_kwargs
        out['read_meth'] = self.read_meth
        return out

    def teardown(self):
        r"""Remove the file."""
        super(TestFileComm, self).teardown()
        self.send_instance.remove_file()

    def test_invalid_read_meth(self):
        r"""Test raise of error on invalid read_meth."""
        kwargs = self.send_inst_kwargs
        kwargs['read_meth'] = 'invalid'
        nt.assert_raises(ValueError, new_comm, self.name, **kwargs)

    @property
    def double_msg(self):
        r"""str: Message that should result from writing two test messages."""
        return 2 * self.test_msg

    def test_append(self):
        r"""Test open of file comm with append."""
        # Write to file
        flag = self.send_instance.send(self.test_msg)
        assert(flag)
        # Open file in append
        kwargs = self.send_inst_kwargs
        kwargs['append'] = True
        new_inst = new_comm('append%s' % self.uuid, **kwargs)
        flag = new_inst.send(self.test_msg)
        assert(flag)
        self.remove_instance(new_inst)
        # Read entire contents
        msg_tot = self.recv_instance.empty_msg
        flag = True
        while flag:
            flag, msg_recv = self.recv_instance.recv()
            if flag:
                msg_tot += msg_recv
            else:
                nt.assert_equal(msg_recv, self.recv_instance.eof_msg)
        nt.assert_equal(msg_tot, self.double_msg)

    def test_work_comm(self):
        r"""Disabled: Test creating/removing a work comm."""
        pass
        
    def test_remaining_bytes(self):
        r"""Test remaining_bytes."""
        nt.assert_equal(self.send_instance.remaining_bytes, 0)
        self.recv_instance.close()
        assert(self.recv_instance.is_closed)
        nt.assert_equal(self.recv_instance.remaining_bytes, 0)

    def test_eof(self):
        r"""Test send/recv of EOF message."""
        self.do_send_recv(send_meth='send_eof', close_on_send_eof=True)

    def test_eof_no_close(self):
        r"""Disabled: Test send/recv of EOF message with no close."""
        pass

    def test_eof_nolimit(self):
        r"""Test send/recv of EOF message through nolimit."""
        self.do_send_recv(send_meth='send_nolimit_eof', close_on_send_eof=True)

    def test_recv_nomsg(self):
        r"""Test recieve when there is no waiting message."""
        flag, msg_recv = self.recv_instance.recv(timeout=self.sleeptime)
        assert(not flag)
        nt.assert_equal(msg_recv, self.recv_instance.eof_msg)


class TestFileComm_readline(TestFileComm):
    r"""Test for FileComm communication class with read_meth = 'readline'."""
    def __init__(self, *args, **kwargs):
        super(TestFileComm_readline, self).__init__(*args, **kwargs)
        self.read_meth = 'readline'
