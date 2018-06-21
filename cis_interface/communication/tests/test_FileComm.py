import os
import nose.tools as nt
from cis_interface.communication import new_comm
from cis_interface.communication.tests import test_CommBase as parent


class TestFileComm(parent.TestCommBase):
    r"""Test for FileComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestFileComm, self).__init__(*args, **kwargs)
        self.comm = 'FileComm'
        self.attr_list += ['fd', 'read_meth', 'append', 'in_temp',
                           'open_as_binary', 'newline', 'is_series',
                           'platform_newline']

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
    def send_inst_kwargs(self):
        r"""dict: Keyword arguments for send instance."""
        out = super(TestFileComm, self).send_inst_kwargs
        out['in_temp'] = True
        return out

    @property
    def append_msg(self):
        r"""str: Message that should be sent by second comm."""
        return self.test_msg
    
    @property
    def double_msg(self):
        r"""str: Message that should result from writing two test messages."""
        out = self.merge_messages([self.test_msg, self.append_msg])
        return out

    def merge_messages(self, msg_list):
        r"""Merge multiple messages to produce the expected total message.

        Args:
            msg_list (list): Messages to be merged.

        Returns:
            obj: Merged message.

        """
        return self.recv_instance.empty_msg.join(msg_list)

    def test_append(self):
        r"""Test open of file comm with append."""
        # Write to file
        flag = self.send_instance.send(self.test_msg)
        assert(flag)
        # Open file in append
        kwargs = self.send_inst_kwargs
        kwargs['append'] = True
        new_inst = new_comm('append%s' % self.uuid, **kwargs)
        flag = new_inst.send(self.append_msg)
        assert(flag)
        self.remove_instance(new_inst)
        # Read entire contents
        flag = True
        msg_list = []
        while flag:
            flag, msg_recv = self.recv_instance.recv()
            if flag:
                msg_list.append(msg_recv)
            else:
                nt.assert_equal(msg_recv, self.recv_instance.eof_msg)
        self.assert_msg_equal(self.merge_messages(msg_list), self.double_msg)

    def test_work_comm(self):
        r"""Disabled: Test creating/removing a work comm."""
        pass

    def test_series(self):
        r"""Test sending/receiving to/from a series of files."""
        # Set up series
        fname = '%d'.join(os.path.splitext(self.send_instance.address))
        self.send_instance.close()
        self.recv_instance.close()
        self.send_instance.is_series = True
        self.recv_instance.is_series = True
        self.send_instance.address = fname
        self.recv_instance.address = fname
        self.send_instance.open()
        self.recv_instance.open()
        # Send/receive multiple messages
        nmsg = 2
        for i in range(nmsg):
            self.do_send_recv()
        
    def test_remaining_bytes(self):
        r"""Test remaining_bytes."""
        nt.assert_equal(self.send_instance.remaining_bytes, 0)
        self.recv_instance.close()
        assert(self.recv_instance.is_closed)
        nt.assert_equal(self.recv_instance.remaining_bytes, 0)

    def test_recv_nomsg(self):
        r"""Test recieve when there is no waiting message."""
        flag, msg_recv = self.recv_instance.recv(timeout=self.sleeptime)
        assert(not flag)
        nt.assert_equal(msg_recv, self.recv_instance.eof_msg)


class TestFileComm_readline(TestFileComm):
    r"""Test for FileComm communication class with read_meth = 'readline'."""

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for tested class."""
        out = super(TestFileComm, self).inst_kwargs
        out['read_meth'] = 'readline'
        return out


class TestFileComm_ascii(TestFileComm):
    r"""Test for FileComm communication class with open_as_binary = False."""

    @property
    def send_inst_kwargs(self):
        r"""dict: Keyword arguments for send instance."""
        out = super(TestFileComm_ascii, self).send_inst_kwargs
        out['open_as_binary'] = False
        return out
