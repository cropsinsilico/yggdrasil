import os
import copy
import unittest
import jsonschema
from yggdrasil.tests import assert_equal
from yggdrasil.communication import new_comm
from yggdrasil.communication.tests import test_CommBase as parent


def test_wait_for_creation():
    r"""Test FileComm waiting for creation."""
    msg_send = b'Test message\n'
    name = 'temp_file_create.txt'
    kwargs = {'in_temp': True, 'comm': 'FileComm', 'dont_open': True}
    # kwargs = {'wait_for_creation': 5, 'in_temp': True, comm='FileComm'}
    send_instance = new_comm(name, direction='send', **kwargs)
    recv_instance = new_comm(name, direction='recv',
                             wait_for_creation=5.0, **kwargs)
    if os.path.isfile(send_instance.address):
        os.remove(send_instance.address)
    
    def open_and_send(inst, msg):
        inst.open()
        flag = inst.send(msg)
        return flag
    
    send_instance.sched_task(0.5, open_and_send, args=[send_instance, msg_send],
                             store_output=True)
    recv_instance.open()
    T = recv_instance.start_timeout(recv_instance.wait_for_creation)
    while (not T.is_out) and (send_instance.sched_out is None):  # pragma: debug
        recv_instance.sleep()
    recv_instance.stop_timeout()
    assert(send_instance.sched_out)
    flag, msg_recv = recv_instance.recv()
    assert(flag)
    assert_equal(msg_recv, msg_send)
    send_instance.close()
    recv_instance.close()
    recv_instance.remove_file()


class TestFileComm(parent.TestCommBase):
    r"""Test for FileComm communication class."""

    comm = 'FileComm'
    attr_list = (copy.deepcopy(parent.TestCommBase.attr_list)
                 + ['fd', 'read_meth', 'append', 'in_temp',
                    'is_series', 'wait_for_creation', 'serializer',
                    'platform_newline'])
    
    def teardown(self):
        r"""Remove the file."""
        super(TestFileComm, self).teardown()
        self.send_instance.remove_file()

    @property
    def send_inst_kwargs(self):
        r"""dict: Keyword arguments for send instance."""
        out = super(TestFileComm, self).send_inst_kwargs
        out['in_temp'] = True
        return out

    def test_send_recv_filter_send_filter(self, **kwargs):
        r"""Test send/recv with filter that blocks send."""
        kwargs.setdefault('msg_recv', self.recv_instance.eof_msg)
        super(TestFileComm, self).test_send_recv_filter_send_filter(**kwargs)
        
    def test_send_recv_filter_recv_filter(self, **kwargs):
        r"""Test send/recv with filter that blocks recv."""
        kwargs.setdefault('msg_recv', self.recv_instance.eof_msg)
        super(TestFileComm, self).test_send_recv_filter_recv_filter(**kwargs)
        
    @unittest.skipIf(True, 'File comm')
    def test_send_recv_nolimit(self):
        r"""Disabled: Test send/recv of a large message."""
        pass  # pragma: no cover

    @unittest.skipIf(True, 'File comm')
    def test_work_comm(self):
        r"""Disabled: Test creating/removing a work comm."""
        pass  # pragma: no cover

    def test_invalid_read_meth(self):
        r"""Test raise of error on invalid read_meth."""
        if self.comm == 'FileComm':
            kwargs = self.send_inst_kwargs
            kwargs['read_meth'] = 'invalid'
            kwargs['skip_component_schema_normalization'] = False
            self.assert_raises(jsonschema.ValidationError, new_comm, self.name,
                               **kwargs)

    def test_append(self):
        r"""Test open of file comm with append."""
        send_objects = self.testing_options['send']
        recv_objects = self.testing_options['recv']
        recv_objects_partial = self.testing_options['recv_partial']
        # Write to file
        flag = self.send_instance.send(send_objects[0])
        assert(flag)
        # Create temp file for receving
        recv_kwargs = copy.deepcopy(self.inst_kwargs)
        recv_kwargs['append'] = True
        new_inst_recv = new_comm('partial%s' % self.uuid, **recv_kwargs)
        self.recv_message_list(new_inst_recv, recv_objects_partial[0],
                               break_on_empty=True)
        # Open file in append
        send_kwargs = copy.deepcopy(self.send_inst_kwargs)
        send_kwargs['append'] = True
        new_inst_send = new_comm('append%s' % self.uuid, **send_kwargs)
        for i in range(1, len(send_objects)):
            flag = new_inst_send.send(send_objects[i])
            assert(flag)
            self.recv_message_list(new_inst_recv, recv_objects_partial[i],
                                   break_on_empty=True)
        self.remove_instance(new_inst_send)
        self.remove_instance(new_inst_recv)
        # Read entire contents
        self.recv_message_list(self.recv_instance, recv_objects)
        # Check file contents
        if self.testing_options.get('exact_contents', True):
            with open(self.send_instance.address, 'rb') as fd:
                contents = fd.read()
            self.assert_equal(contents, self.testing_options['contents'])

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
        self.assert_equal(self.send_instance.remaining_bytes, 0)
        self.recv_instance.close()
        assert(self.recv_instance.is_closed)
        self.assert_equal(self.recv_instance.remaining_bytes, 0)

    def test_recv_nomsg(self):
        r"""Test recieve when there is no waiting message."""
        flag, msg_recv = self.recv_instance.recv(timeout=self.sleeptime)
        assert(not flag)
        self.assert_equal(msg_recv, self.recv_instance.eof_msg)


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
