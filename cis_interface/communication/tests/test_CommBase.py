import nose.tools as nt
import os
# from cis_interface.tools import CisClass
from cis_interface.tests import CisTest, IOInfo
from cis_interface.communication import new_comm, get_comm_class


class TestCommBase(CisTest, IOInfo):
    r"""Tests for CommBase communication class.

    Attributes:
        send_inst_kwargs (dict): Keyword arguments for send half of the comm
            pair.

    """
    def __init__(self, *args, **kwargs):
        super(TestCommBase, self).__init__(*args, **kwargs)
        IOInfo.__init__(self)
        self.comm = 'CommBase'
        self.attr_list += ['name', 'address', 'direction', 'format_str',
                           'meth_deserialize', 'meth_serialize', 'recv_timeout',
                           'close_on_eof_recv']

    @property
    def name(self):
        r"""str: Name of the test connection."""
        return 'Test%s_%s' % (self.cls, self.uuid)

    @property
    def cls(self):
        r"""str: Communication class."""
        return self.comm

    @property
    def mod(self):
        r"""str: Absolute module import."""
        return 'cis_interface.communication.%s' % self.cls

    @property
    def send_inst_kwargs(self):
        r"""dict: Keyword arguments for send instance."""
        return {'comm': self.comm, 'reverse_names': True, 'direction': 'send'}

    @property
    def inst_args(self):
        r"""list: Arguments for tested class."""
        return [self.name]

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for tested class."""
        return self.send_instance.opp_comm_kwargs()

    @property
    def recv_instance(self):
        r"""Alias for instance."""
        return self.instance

    @property
    def maxMsgSize(self):
        r"""int: Maximum message size."""
        return max(self.instance.maxMsgSize,
                   super(TestCommBase, self).maxMsgSize)

    @property
    def comm_count(self):
        r"""int: Return the number of comms."""
        out = 0
        comms = set([self.comm, self.send_inst_kwargs['comm']])
        for x in comms:
            cls = get_comm_class(x)
            out += cls.comm_count()
        return out

    @property
    def test_msg(self):
        r"""str: Test message that should be used for any send/recv tests."""
        return self.msg_short
        
    def setup(self, *args, **kwargs):
        r"""Initialize comm object pair."""
        self.nprev_comm = self.comm_count
        self.send_instance = new_comm(self.name, **self.send_inst_kwargs)
        super(TestCommBase, self).setup(*args, **kwargs)
        # CommBase is dummy class that never opens
        if self.comm == 'CommBase':
            assert(not self.send_instance.is_open)
            assert(not self.recv_instance.is_open)
        else:
            assert(self.send_instance.is_open)
            assert(self.recv_instance.is_open)

    def teardown(self, *args, **kwargs):
        r"""Destroy comm object pair."""
        self.remove_instance(self.send_instance)
        super(TestCommBase, self).teardown(*args, **kwargs)
        # x = CisClass(self.name, timeout=self.timeout, sleeptime=self.sleeptime)
        # Tout = x.start_timeout()
        # while (not Tout.is_out) and (self.comm_count > self.nprev_comm):
        #     x.sleep()
        # x.stop_timeout()
        nt.assert_equal(self.comm_count, self.nprev_comm)

    def remove_instance(self, inst):
        r"""Remove an instance."""
        inst.close()
        assert(inst.is_closed)
        super(TestCommBase, self).remove_instance(inst)

    def get_fresh_error_instance(self):
        r"""Get comm instance with ErrorClass parent class."""
        kwargs = self.send_inst_kwargs
        kwargs.update(base_comm=kwargs['comm'], new_comm_class='ErrorComm')
        inst = new_comm(self.name + '_' + self.uuid, **kwargs)
        return inst

    def test_error_send(self):
        r"""Test error on send."""
        inst = self.get_fresh_error_instance()
        inst.error_replace('send_multipart')
        flag = inst.send(self.msg_short)
        assert(not flag)
        inst.restore_all()
        inst.close()

    def test_double_open(self):
        r"""Test that opening twice dosn't cause errors."""
        self.send_instance.open()
        self.recv_instance.open()

    def test_send_recv_after_close(self):
        r"""Test that send/recv after close returns false."""
        self.send_instance.close()
        self.recv_instance.close()
        assert(self.send_instance.is_closed)
        assert(self.recv_instance.is_closed)
        flag = self.send_instance.send(self.msg_short)
        assert(not flag)
        flag, msg_recv = self.recv_instance.recv()
        assert(not flag)

    def test_attributes(self):
        r"""Assert that the instance has all of the required attributes."""
        for a in self.attr_list:
            if not hasattr(self.instance, a):  # pragma: debug
                raise AttributeError("Driver does not have attribute %s" % a)

    def test_invalid_direction(self):
        r"""Check that error raised for invalid direction."""
        kwargs = self.send_inst_kwargs
        kwargs['direction'] = 'invalid'
        nt.assert_raises(ValueError, new_comm, self.name, **kwargs)

    def test_opp_comm_kwargs(self):
        r"""Test getting keyword arguments for the opposite comm."""
        self.instance.opp_comm_kwargs()

    def test_work_comm(self):
        r"""Test creating/removing a work comm."""
        header_send = dict(id=self.uuid + '0')
        wc_send = self.instance.create_work_comm(header_send)
        nt.assert_raises(KeyError, self.instance.add_work_comm,
                         header_send['id'], wc_send)
        # Create recv instance in way that tests new_comm
        header_recv = dict(id=self.uuid + '1', address=wc_send.address)
        recv_kwargs = self.instance.get_work_comm_kwargs
        recv_kwargs['work_comm_name'] = 'test_worker_%s' % header_recv['id']
        recv_kwargs['new_comm_class'] = wc_send.comm_class
        os.environ[recv_kwargs['work_comm_name']] = wc_send.opp_address
        wc_recv = self.instance.create_work_comm(header_recv, **recv_kwargs)
        # wc_recv = self.instance.get_work_comm(header_recv)
        if self.comm == 'CommBase':
            flag = wc_send.send(self.test_msg)
            assert(not flag)
            flag, msg_recv = wc_recv.recv()
            assert(not flag)
        else:
            flag = wc_send.send(self.test_msg)
            assert(flag)
            flag, msg_recv = wc_recv.recv(self.timeout)
            assert(flag)
            nt.assert_equal(msg_recv, self.test_msg)
            # Assert errors on second attempt
            nt.assert_raises(RuntimeError, wc_send.send, self.test_msg)
            nt.assert_raises(RuntimeError, wc_recv.recv)
        self.instance.remove_work_comm(header_send['id'])
        self.instance.remove_work_comm(header_recv['id'])

    def test_eof(self):
        r"""Test send/recv of EOF message."""
        if self.comm != 'CommBase':
            flag = self.send_instance.send(self.send_instance.eof_msg)
            assert(flag)
            flag, msg_recv = self.recv_instance.recv(timeout=self.timeout)
            assert(not flag)
            nt.assert_equal(msg_recv, self.send_instance.eof_msg)
            assert(self.recv_instance.is_closed)

    def test_eof_nolimit(self):
        r"""Test send/recv of EOF message through nolimit."""
        if self.comm != 'CommBase':
            flag = self.send_instance.send_nolimit(self.send_instance.eof_msg)
            assert(flag)
            flag, msg_recv = self.recv_instance.recv_nolimit(timeout=self.timeout)
            assert(not flag)
            nt.assert_equal(msg_recv, self.send_instance.eof_msg)
            assert(self.recv_instance.is_closed)

    def do_send_recv(self, send_meth='send', recv_meth='recv', msg_send=None):
        r"""Generic send/recv of a message."""
        if msg_send is None:
            msg_send = self.test_msg
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)
        fsend_meth = getattr(self.send_instance, send_meth)
        frecv_meth = getattr(self.recv_instance, recv_meth)
        if self.comm == 'CommBase':
            flag = fsend_meth(msg_send)
            assert(not flag)
            flag, msg_recv = frecv_meth()
            assert(not flag)
        else:
            flag = fsend_meth(msg_send)
            assert(flag)
            T = self.recv_instance.start_timeout()
            while (not T.is_out) and (self.recv_instance.n_msg == 0):
                self.recv_instance.sleep()
            self.recv_instance.stop_timeout()
            assert(self.recv_instance.n_msg >= 1)
            # IPC nolimit sends multiple messages
            # nt.assert_equal(self.recv_instance.n_msg, 1)
            flag, msg_recv = frecv_meth()
            assert(flag)
            nt.assert_equal(msg_recv, msg_send)
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)

    def test_send_recv(self):
        r"""Test send/recv of a small message."""
        self.do_send_recv()

    def test_send_recv_nolimit(self):
        r"""Test send/recv of a large message."""
        if self.comm != 'AsciiTableComm':
            assert(len(self.msg_long) > self.maxMsgSize)
        self.do_send_recv('send_nolimit', 'recv_nolimit', self.msg_long)

    def test_send_recv_line(self):
        r"""Test send/recv of a line message."""
        self.do_send_recv('send_line', 'recv_line')
        
    def test_send_recv_row(self):
        r"""Test send/recv of a row message."""
        self.do_send_recv('send_row', 'recv_row')
        
    def test_send_recv_array(self):
        r"""Test send/recv of a array message."""
        self.do_send_recv('send_array', 'recv_array')

    def test_purge(self):
        r"""Test purging messages from the comm."""
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)
        # Purge recv while open
        if self.comm != 'CommBase':
            flag = self.send_instance.send(self.msg_short)
            assert(flag)
            T = self.recv_instance.start_timeout()
            while (not T.is_out) and (self.recv_instance.n_msg == 0):
                self.recv_instance.sleep()
            self.recv_instance.stop_timeout()
            nt.assert_equal(self.recv_instance.n_msg, 1)
        self.recv_instance.purge()
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)
        # Purge recv while closed
        self.recv_instance.close()
        self.recv_instance.purge()
