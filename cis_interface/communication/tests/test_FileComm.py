import os
import unittest
import nose.tools as nt
from cis_interface.communication import new_comm
from cis_interface.communication.tests import test_CommBase as parent


class TestFileComm(parent.TestCommBase):
    r"""Test for FileComm communication class."""

    comm = 'FileComm'
    
    def __init__(self, *args, **kwargs):
        super(TestFileComm, self).__init__(*args, **kwargs)
        self.attr_list += ['fd', 'read_meth', 'append', 'in_temp',
                           'open_as_binary', 'newline', 'is_series',
                           'platform_newline']
        self._testing_options = None

    def teardown(self):
        r"""Remove the file."""
        super(TestFileComm, self).teardown()
        self.send_instance.remove_file()

    @property
    def send_inst_kwargs(self):
        r"""dict: Keyword arguments for send instance."""
        out = super(TestFileComm, self).send_inst_kwargs
        out['in_temp'] = True
        out.update(self.testing_options['kwargs'])
        return out

    def get_testing_options(self):
        r"""Get testing options."""
        return self.import_cls.get_testing_options()

    @property
    def testing_options(self):
        r"""dict: Testing options."""
        if getattr(self, '_testing_options', None) is None:
            self._testing_options = self.get_testing_options()
        return self._testing_options

    @property
    def test_msg(self):
        r"""str: Test message that should be used for any send/recv tests."""
        return self.testing_options['msg']

    @unittest.skipIf(True, 'File comm')
    def test_send_recv_nolimit(self):
        r"""Disabled: Test send/recv of a large message."""
        pass

    @unittest.skipIf(True, 'File comm')
    def test_work_comm(self):
        r"""Disabled: Test creating/removing a work comm."""
        pass

    def test_invalid_read_meth(self):
        r"""Test raise of error on invalid read_meth."""
        kwargs = self.send_inst_kwargs
        kwargs['read_meth'] = 'invalid'
        nt.assert_raises(ValueError, new_comm, self.name, **kwargs)

    def test_send_recv_dict(self):
        r"""Test send/recv message as dict."""
        msg_send = self.testing_options['dict']
        self.do_send_recv(send_meth='send_dict', recv_meth='recv_dict',
                          msg_send=msg_send)
        
    def test_append(self):
        r"""Test open of file comm with append."""
        send_objects = self.testing_options['send']
        recv_objects = self.testing_options['recv']
        # Write to file
        flag = self.send_instance.send(send_objects[0])
        assert(flag)
        # Open file in append
        kwargs = self.send_inst_kwargs
        kwargs['append'] = True
        new_inst = new_comm('append%s' % self.uuid, **kwargs)
        for x in send_objects[1:]:
            flag = new_inst.send(x)
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
        nt.assert_equal(len(msg_list), len(recv_objects))
        for x, y in zip(msg_list, recv_objects):
            self.assert_msg_equal(x, y)
        # Check file contents
        if self.testing_options.get('exact_contents', True):
            with open(self.send_instance.address, 'rb') as fd:
                contents = fd.read()
            nt.assert_equal(contents, self.testing_options['contents'])

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

    def test_is_installed(self):
        r"""Test class is_installed method."""
        assert(self.import_cls.is_installed(language='invalid'))


class TestFileComm_readline(TestFileComm):
    r"""Test for FileComm communication class with read_meth = 'readline'."""

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for tested class."""
        out = super(TestFileComm, self).inst_kwargs
        out['read_meth'] = 'readline'
        return out

    @property
    def testing_options(self):
        r"""dict: Testing options."""
        out = super(TestFileComm_readline, self).testing_options
        out['recv'] = out['send']
        return out

    
class TestFileComm_ascii(TestFileComm):
    r"""Test for FileComm communication class with open_as_binary = False."""

    @property
    def send_inst_kwargs(self):
        r"""dict: Keyword arguments for send instance."""
        out = super(TestFileComm_ascii, self).send_inst_kwargs
        out['open_as_binary'] = False
        return out
