import uuid
import copy
from yggdrasil.communication.tests import test_CommBase as parent


class TestForkComm(parent.TestCommBase):
    r"""Tests for ForkComm communication class."""

    comm = 'ForkComm'
    attr_list = (copy.deepcopy(parent.TestCommBase.attr_list)
                 + ['comm_list', 'curr_comm_index'])
    ncomm = 2
    send_pattern = None
    recv_pattern = None
    test_error_send = None
    test_error_recv = None
    test_work_comm = None

    @property
    def cleanup_comm_classes(self):
        r"""list: Comm classes that should be cleaned up following the test."""
        return set([self.comm] + [None])

    @property
    def send_inst_kwargs(self):
        r"""dict: Keyword arguments for send instance."""
        out = super(TestForkComm, self).send_inst_kwargs
        out['ncomm'] = self.ncomm
        out['pattern'] = self.send_pattern
        return out

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for tested class."""
        out = super(TestForkComm, self).inst_kwargs
        out['pattern'] = self.recv_pattern
        return out

    def map_sent2recv(self, obj):
        r"""Convert a sent object into a received one."""
        if (((self.send_instance.pattern == 'scatter')
             and isinstance(obj, list) and obj)):
            single_obj = obj[0]
        else:
            single_obj = obj
        if self.recv_instance.pattern == 'gather':
            if obj in [b'', []]:
                return []
            return [single_obj for _ in range(self.ncomm)]
        return single_obj

    def duplicate_msg(self, out, direction='send'):
        r"""Copy a message for 'scatter' communication pattern."""
        if ((((direction == 'send')
              and (self.send_instance.pattern == 'scatter'))
             or ((direction == 'recv')
                 and (self.recv_instance.pattern == 'gather')))):
            out = [out for _ in range(self.ncomm)]
        return out
        
    @property
    def test_msg(self):
        r"""str: Test message that should be used for any send/recv tests."""
        return self.duplicate_msg(super(TestForkComm, self).test_msg)

    @property
    def test_msg_array(self):
        r"""str: Test message that should be used for any send/recv tests."""
        return self.duplicate_msg(super(TestForkComm, self).test_msg_array)

    @property
    def test_msg_dict(self):
        r"""dict: Test message that should be used for send_dict/recv_dict
        tests."""
        return self.duplicate_msg(super(TestForkComm, self).test_msg_dict)

    @property
    def msg_long(self):
        r"""str: Small test message for sending."""
        out = super(TestForkComm, self).test_msg
        if isinstance(out, bytes):
            out += (self.maxMsgSize * b'0')
        return self.duplicate_msg(out)
        
    @property
    def msg_filter_send(self):
        r"""object: Message to filter out on the send side."""
        return self.duplicate_msg(super(TestForkComm, self).msg_filter_send)
            
    @property
    def msg_filter_recv(self):
        r"""object: Message to filter out on the recv side."""
        return self.duplicate_msg(super(TestForkComm, self).msg_filter_recv)
        
    def test_error_name(self):
        r"""Test error on missing address."""
        self.assert_raises(RuntimeError, self.import_cls, 'test%s' % uuid.uuid4())

    def do_send_recv(self, *args, **kwargs):
        r"""Generic send/recv of a message."""
        if ((('eof' not in kwargs.get('send_meth', 'None'))
             and (not kwargs.get('no_recv', False))
             and (self.send_instance.pattern in ['broadcast', 'scatter'])
             and (self.recv_instance.pattern == 'cycle'))):
            kwargs.setdefault('n_recv', self.ncomm)
        super(TestForkComm, self).do_send_recv(*args, **kwargs)

    def test_send_recv_filter_eof(self, **kwargs):
        r"""Test send/recv of EOF with filter."""
        kwargs.setdefault('recv_timeout', 2 * self.timeout)
        super(TestForkComm, self).test_send_recv_filter_eof(**kwargs)
        
    def test_send_recv_filter_recv_filter(self, **kwargs):
        r"""Test send/recv with filter that blocks recv."""
        kwargs.setdefault('n_recv', 1)
        super(TestForkComm, self).test_send_recv_filter_recv_filter(**kwargs)
        
    def test_purge(self, **kwargs):
        r"""Test purging messages from the comm."""
        if self.send_instance.pattern == 'scatter':
            kwargs['msg_recv'] = [self.test_msg for _ in range(self.ncomm)]
        if (((self.send_instance.pattern in ['broadcast', 'scatter'])
             and (self.recv_instance.pattern == 'cycle'))):
            kwargs['nrecv'] = self.ncomm
        super(TestForkComm, self).test_purge(**kwargs)
        
    def test_send_recv_after_close(self, **kwargs):
        r"""Test that opening twice dosn't cause errors and that send/recv after
        close returns false."""
        kwargs.setdefault('msg_send', [self.test_msg for _ in range(self.ncomm)])
        super(TestForkComm, self).test_send_recv_after_close(**kwargs)


class TestForkCommList(TestForkComm):
    r"""Tests for ForkComm communication class with construction from address."""
    @property
    def inst_kwargs(self):
        r"""list: Keyword arguments for tested class."""
        out = super(TestForkComm, self).inst_kwargs
        out['comm_list'] = None  # To force test of construction from addresses
        return out


class TestForkCommCycle(TestForkComm):
    r"""Tests for ForkComm communication class with cycle/cycle communication
    pattern."""

    send_pattern = 'cycle'
    recv_pattern = 'cycle'


class TestForkCommScatter(TestForkComm):
    r"""Tests for ForkComm communication class with scatter/gather
    communication pattern."""
    
    send_pattern = 'scatter'
    recv_pattern = 'gather'

    def test_async_gather(self):
        r"""Test scatter-gather w/ intermittent send."""
        test_msg = self.test_msg
        self.send_instance.comm_list[0].send(test_msg[0])
        flag, msg_recv = self.recv_instance.recv()
        assert(flag)
        assert(self.recv_instance.is_empty_recv(msg_recv))
        for msg_send, comm in zip(test_msg[1:], self.send_instance.comm_list[1:]):
            assert(comm.send(msg_send))
        flag, msg_recv = self.recv_instance.recv()
        assert(flag)
        self.assert_msg_equal(msg_recv, test_msg)
