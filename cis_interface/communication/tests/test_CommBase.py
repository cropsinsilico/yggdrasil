import os
import uuid
import nose.tools as nt
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
                           'close_on_eof_recv', 'opp_address', 'opp_comms',
                           'maxMsgSize']

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
    def is_installed(self):
        r"""bool: Is the communication class installed."""
        return self.import_cls.is_installed()

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
        return self.instance.maxMsgSize

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
        assert(self.is_installed)
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

    # def create_instance(self):
    #     r"""Create a new instance of the class."""
    #     inst = new_comm(*self.inst_args, **self.inst_kwargs)
    #     return inst

    def remove_instance(self, inst):
        r"""Remove an instance."""
        inst.close()
        assert(inst.is_closed)
        super(TestCommBase, self).remove_instance(inst)

    def get_fresh_error_instance(self, recv=False):
        r"""Get comm instance with ErrorClass parent class."""
        kwargs = self.send_inst_kwargs
        if recv:
            kwargs['direction'] = 'recv'
        kwargs.update(base_comm=kwargs['comm'], new_comm_class='ErrorComm')
        inst = new_comm(self.name + '_' + self.uuid, **kwargs)
        return inst

    def test_maxMsgSize(self):
        r"""Print maxMsgSize."""
        self.instance.debug('maxMsgSize: %d, %d, %d', self.maxMsgSize,
                            self.send_instance.maxMsgSize,
                            self.recv_instance.maxMsgSize)

    def test_error_name(self):
        r"""Test error on missing address."""
        nt.assert_raises(RuntimeError, self.import_cls, 'test%s' % uuid.uuid4())

    def test_error_send(self):
        r"""Test error on send."""
        inst = self.get_fresh_error_instance()
        inst._first_send_done = True
        inst.error_replace('send_multipart')
        flag = inst.send(self.msg_short)
        assert(not flag)
        inst.restore_all()
        inst.close()

    def test_error_recv(self):
        r"""Test error on recv."""
        inst = self.get_fresh_error_instance(recv=True)
        inst.error_replace('recv_multipart')
        flag, msg_recv = inst.recv()
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
            if not hasattr(self.send_instance, a):  # pragma: debug
                raise AttributeError("Send comm does not have attribute %s" % a)
            if not hasattr(self.recv_instance, a):  # pragma: debug
                raise AttributeError("Recv comm does not have attribute %s" % a)

    def test_invalid_direction(self):
        r"""Check that error raised for invalid direction."""
        kwargs = self.send_inst_kwargs
        kwargs['direction'] = 'invalid'
        nt.assert_raises(ValueError, new_comm, self.name + "_" + self.uuid,
                         **kwargs)

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
        # Create work comm that should be cleaned up on teardown
        self.instance.get_header(self.test_msg)

    def do_send_recv(self, send_meth='send', recv_meth='recv', msg_send=None,
                     reverse_comms=False, send_kwargs=None, recv_kwargs=None,
                     close_on_send_eof=False, close_on_recv_eof=True):
        r"""Generic send/recv of a message."""
        is_eof = ('eof' in send_meth)
        if msg_send is None:
            if is_eof:
                msg_send = self.send_instance.eof_msg
            else:
                msg_send = self.test_msg
        if send_kwargs is None:
            send_kwargs = dict()
        if recv_kwargs is None:
            recv_kwargs = dict()
        if is_eof:
            send_args = tuple()
        else:
            send_args = (msg_send,)
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)
        if reverse_comms:
            send_instance = self.recv_instance
            recv_instance = self.send_instance
        else:
            send_instance = self.send_instance
            recv_instance = self.recv_instance
        recv_instance.close_on_eof_recv = close_on_recv_eof
        fsend_meth = getattr(send_instance, send_meth)
        frecv_meth = getattr(recv_instance, recv_meth)
        if self.comm == 'CommBase':
            flag = fsend_meth(*send_args, **send_kwargs)
            assert(not flag)
            flag, msg_recv = frecv_meth(**recv_kwargs)
            assert(not flag)
            nt.assert_raises(NotImplementedError, self.recv_instance._send, self.test_msg)
            nt.assert_raises(NotImplementedError, self.recv_instance._recv)
        else:
            flag = fsend_meth(*send_args, **send_kwargs)
            if is_eof and close_on_send_eof:
                assert(not flag)
                assert(send_instance.is_closed)
            else:
                assert(flag)
            if not is_eof:
                T = recv_instance.start_timeout(recv_instance.recv_timeout)
                while (not T.is_out) and (recv_instance.n_msg == 0):  # pragma: debug
                    recv_instance.sleep()
                recv_instance.stop_timeout()
                assert(recv_instance.n_msg >= 1)
                # IPC nolimit sends multiple messages
                # nt.assert_equal(recv_instance.n_msg, 1)
            flag, msg_recv = frecv_meth(timeout=self.timeout, **recv_kwargs)
            if is_eof and close_on_recv_eof:
                assert(not flag)
                assert(recv_instance.is_closed)
            else:
                assert(flag)
            nt.assert_equal(msg_recv, msg_send)
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)

    def test_recv_nomsg(self):
        r"""Test recieve when there is no waiting message."""
        flag, msg_recv = self.recv_instance.recv(timeout=self.sleeptime)
        if self.comm == 'CommBase':
            assert(not flag)
        else:
            assert(flag)
        assert(not msg_recv)

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

    def test_eof(self):
        r"""Test send/recv of EOF message."""
        self.do_send_recv(send_meth='send_eof')

    def test_eof_no_close(self):
        r"""Test send/recv of EOF message with no close."""
        self.do_send_recv(send_meth='send_eof', close_on_recv_eof=False)

    def test_eof_nolimit(self):
        r"""Test send/recv of EOF message through nolimit."""
        self.do_send_recv(send_meth='send_nolimit_eof')

    def test_purge(self):
        r"""Test purging messages from the comm."""
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)
        # Purge recv while open
        if self.comm != 'CommBase':
            flag = self.send_instance.send(self.msg_short)
            assert(flag)
            T = self.recv_instance.start_timeout()
            while (not T.is_out) and (self.recv_instance.n_msg == 0):  # pragma: debug
                self.recv_instance.sleep()
            self.recv_instance.stop_timeout()
            nt.assert_greater(self.recv_instance.n_msg, 0)
        self.recv_instance.purge()
        # Uni-directional comms can't know about messages sent
        # nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)
        # Purge recv while closed
        self.recv_instance.close()
        self.recv_instance.purge()
