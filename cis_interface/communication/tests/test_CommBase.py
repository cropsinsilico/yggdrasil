import os
import uuid
import nose.tools as nt
from cis_interface.tests import CisTestClassInfo
from cis_interface.communication import new_comm, get_comm, CommBase


def test_registry():
    r"""Test registry of comm."""
    comm_class = 'CommBase'
    key = 'key1'
    value = None
    assert(not CommBase.is_registered(comm_class, key))
    assert(not CommBase.unregister_comm(comm_class, key))
    nt.assert_equal(CommBase.get_comm_registry(None), {})
    nt.assert_equal(CommBase.get_comm_registry(comm_class), {})
    CommBase.register_comm(comm_class, key, value)
    assert(key in CommBase.get_comm_registry(comm_class))
    assert(CommBase.is_registered(comm_class, key))
    assert(not CommBase.unregister_comm(comm_class, key, dont_close=True))
    CommBase.register_comm(comm_class, key, value)
    assert(not CommBase.unregister_comm(comm_class, key))


class TestCommBase(CisTestClassInfo):
    r"""Tests for CommBase communication class.

    Attributes:
        send_inst_kwargs (dict): Keyword arguments for send half of the comm
            pair.

    """
    def __init__(self, *args, **kwargs):
        super(TestCommBase, self).__init__(*args, **kwargs)
        self.comm = 'CommBase'
        self.attr_list += ['name', 'address', 'direction',
                           'serializer', 'recv_timeout',
                           'close_on_eof_recv', 'opp_address', 'opp_comms',
                           'maxMsgSize']

    @property
    def cleanup_comm_classes(self):
        r"""list: Comm classes that should be cleaned up following the test."""
        return set([self.comm, self.send_inst_kwargs['comm']])

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
    def test_msg(self):
        r"""str: Test message that should be used for any send/recv tests."""
        return self.msg_short
        
    def setup(self, *args, **kwargs):
        r"""Initialize comm object pair."""
        assert(self.is_installed)
        sleep_after_connect = kwargs.pop('sleep_after_connect', False)
        send_inst_kwargs = self.send_inst_kwargs
        kwargs.setdefault('nprev_comm', self.comm_count)
        kwargs.setdefault('nprev_fd', self.fd_count)
        self.send_instance = new_comm(self.name, **send_inst_kwargs)
        super(TestCommBase, self).setup(*args, **kwargs)
        if sleep_after_connect:
            self.send_instance.sleep()
        # CommBase is dummy class that never opens
        if self.comm in ['CommBase', 'AsyncComm']:
            assert(not self.send_instance.is_open)
            assert(not self.recv_instance.is_open)
        else:
            assert(self.send_instance.is_open)
            assert(self.recv_instance.is_open)

    def teardown(self, *args, **kwargs):
        r"""Destroy comm object pair."""
        self.remove_instance(self.send_instance)
        super(TestCommBase, self).teardown(*args, **kwargs)

    def create_instance(self):
        r"""Create a new instance of the class."""
        inst = get_comm(*self.inst_args, **self.inst_kwargs)
        assert(isinstance(inst, self.import_cls))
        return inst

    def remove_instance(self, inst):
        r"""Remove an instance."""
        inst.close()
        assert(inst.is_closed)
        super(TestCommBase, self).remove_instance(inst)

    def get_fresh_error_instance(self, recv=False):
        r"""Get comm instance with ErrorClass parent class."""
        send_kwargs = self.send_inst_kwargs
        err_kwargs = dict(base_comm=send_kwargs['comm'], new_comm_class='ErrorComm')
        err_name = self.name + '_' + self.uuid
        if not recv:
            send_kwargs.update(**err_kwargs)
        send_inst = new_comm(err_name, **send_kwargs)
        recv_kwargs = send_inst.opp_comm_kwargs()
        recv_kwargs['comm'] = send_kwargs['comm']
        if recv:
            recv_kwargs.update(**err_kwargs)
        recv_inst = new_comm(err_name, **recv_kwargs)
        return send_inst, recv_inst

    def test_empty_msg(self):
        r"""Test identification of empty message."""
        msg = self.instance.empty_obj_recv
        assert(self.instance.is_empty_recv(msg))
        assert(not self.instance.is_empty_recv(self.instance.eof_msg))
        if self.recv_instance.recv_converter is None:
            self.recv_instance.recv_converter = lambda x: x
            msg = self.instance.empty_obj_recv
            assert(self.instance.is_empty_recv(msg))
            assert(not self.instance.is_empty_recv(self.instance.eof_msg))
            
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
        send_inst, recv_inst = self.get_fresh_error_instance()
        send_inst._first_send_done = True
        send_inst.error_replace('send_multipart')
        flag = send_inst.send(self.msg_short)
        assert(not flag)
        send_inst.restore_all()
        send_inst.close()
        recv_inst.close()

    def test_error_recv(self):
        r"""Test error on recv."""
        self.fd_count
        send_inst, recv_inst = self.get_fresh_error_instance(recv=True)
        self.fd_count
        recv_inst.error_replace('recv_multipart')
        flag, msg_recv = recv_inst.recv()
        self.fd_count
        assert(not flag)
        recv_inst.restore_all()
        send_inst.close()
        recv_inst.close()
        self.fd_count

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
        wc_send = self.instance.create_work_comm()
        nt.assert_raises(KeyError, self.instance.add_work_comm, wc_send)
        # Create recv instance in way that tests new_comm
        header_recv = dict(id=self.uuid + '1', address=wc_send.address)
        recv_kwargs = self.instance.get_work_comm_kwargs
        recv_kwargs['work_comm_name'] = 'test_worker_%s' % header_recv['id']
        recv_kwargs['new_comm_class'] = wc_send.comm_class
        os.environ[recv_kwargs['work_comm_name']] = wc_send.opp_address
        wc_recv = self.instance.create_work_comm(**recv_kwargs)
        # wc_recv = self.instance.get_work_comm(header_recv)
        if self.comm in ['CommBase', 'AsyncComm']:
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
            # nt.assert_raises(RuntimeError, wc_send.send, self.test_msg)
            nt.assert_raises(RuntimeError, wc_recv.recv)
        self.instance.remove_work_comm(wc_send.uuid)
        self.instance.remove_work_comm(wc_recv.uuid)
        self.instance.remove_work_comm(wc_recv.uuid)
        # Create work comm that should be cleaned up on teardown
        self.instance.create_work_comm()

    def map_sent2recv(self, obj):
        r"""Convert a sent object into a received one."""
        return obj

    def assert_msg_equal(self, x, y):
        r"""Assert that two messages are equivalent."""
        if y == self.send_instance.eof_msg:
            nt.assert_equal(x, y)
        else:
            nt.assert_equal(x, self.map_sent2recv(y))

    def do_send_recv(self, send_meth='send', recv_meth='recv', msg_send=None,
                     n_msg_send_meth='n_msg_send', n_msg_recv_meth='n_msg_recv',
                     reverse_comms=False, send_kwargs=None, recv_kwargs=None,
                     n_send=1, n_recv=1,
                     close_on_send_eof=None, close_on_recv_eof=None):
        r"""Generic send/recv of a message."""
        tkey = 'do_send_recv'
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
        nt.assert_equal(getattr(self.send_instance, n_msg_send_meth), 0)
        nt.assert_equal(getattr(self.recv_instance, n_msg_recv_meth), 0)
        if reverse_comms:
            send_instance = self.recv_instance
            recv_instance = self.send_instance
        else:
            send_instance = self.send_instance
            recv_instance = self.recv_instance
        if close_on_recv_eof is None:
            close_on_recv_eof = recv_instance.close_on_eof_recv
        if close_on_send_eof is None:
            close_on_send_eof = send_instance.close_on_eof_send
        recv_instance.close_on_eof_recv = close_on_recv_eof
        send_instance.close_on_eof_send = close_on_send_eof
        if self.comm == 'ForkComm':
            for x in recv_instance.comm_list:
                x.close_on_eof_recv = close_on_recv_eof
            for x in send_instance.comm_list:
                x.close_on_eof_send = close_on_send_eof
        fsend_meth = getattr(send_instance, send_meth)
        frecv_meth = getattr(recv_instance, recv_meth)
        if self.comm in ['CommBase', 'AsyncComm']:
            flag = fsend_meth(*send_args, **send_kwargs)
            assert(not flag)
            flag, msg_recv = frecv_meth(**recv_kwargs)
            assert(not flag)
            if self.comm == 'CommBase':
                nt.assert_raises(NotImplementedError, self.recv_instance._send,
                                 self.test_msg)
                nt.assert_raises(NotImplementedError, self.recv_instance._recv)
        else:
            for i in range(n_send):
                flag = fsend_meth(*send_args, **send_kwargs)
                assert(flag)
            # Wait for messages to be received
            for i in range(n_recv):
                if not is_eof:
                    T = recv_instance.start_timeout(self.timeout, key_suffix=tkey)
                    while ((not T.is_out) and (not recv_instance.is_closed) and
                           (getattr(recv_instance,
                                    n_msg_recv_meth) == 0)):  # pragma: debug
                        recv_instance.sleep()
                    recv_instance.stop_timeout(key_suffix=tkey)
                    assert(getattr(recv_instance, n_msg_recv_meth) >= 1)
                    # IPC nolimit sends multiple messages
                    # nt.assert_equal(recv_instance.n_msg_recv, 1)
                flag, msg_recv = frecv_meth(timeout=self.timeout, **recv_kwargs)
                if is_eof and close_on_recv_eof:
                    assert(not flag)
                    assert(recv_instance.is_closed)
                else:
                    assert(flag)
                self.assert_msg_equal(msg_recv, msg_send)
            # Wait for send to close
            if is_eof and close_on_send_eof:
                T = send_instance.start_timeout(self.timeout, key_suffix=tkey)
                while (not T.is_out) and (not send_instance.is_closed):  # pragma: debug
                    send_instance.sleep()
                send_instance.stop_timeout(key_suffix=tkey)
                assert(send_instance.is_closed)
        # Make sure no messages outgoing
        T = send_instance.start_timeout(self.timeout, key_suffix=tkey)
        while ((not T.is_out) and
               (getattr(send_instance, n_msg_send_meth) != 0)):  # pragma: debug
            send_instance.sleep()
        send_instance.stop_timeout(key_suffix=tkey)
        # Print status of comms
        send_instance.printStatus()
        recv_instance.printStatus()
        # Confirm recept of messages
        if not (is_eof or reverse_comms):
            send_instance.wait_for_confirm(timeout=self.timeout)
            recv_instance.wait_for_confirm(timeout=self.timeout)
            assert(send_instance.is_confirmed)
            assert(recv_instance.is_confirmed)
            send_instance.confirm(noblock=True)
            recv_instance.confirm(noblock=True)
        nt.assert_equal(getattr(send_instance, n_msg_send_meth), 0)
        nt.assert_equal(getattr(recv_instance, n_msg_recv_meth), 0)

    def test_drain_messages(self):
        r"""Test waiting for messages to drain."""
        self.send_instance.drain_messages(timeout=self.timeout)
        nt.assert_equal(self.send_instance.n_msg_send_drain, 0)
        if not self.recv_instance.is_file:
            self.recv_instance.drain_messages(timeout=self.timeout)
            nt.assert_equal(self.recv_instance.n_msg_recv_drain, 0)
        nt.assert_raises(ValueError, self.send_instance.drain_messages,
                         variable='n_msg_invalid')
        nt.assert_raises(ValueError, self.recv_instance.drain_messages,
                         variable='n_msg_invalid')

    def test_recv_nomsg(self):
        r"""Test recieve when there is no waiting message."""
        flag, msg_recv = self.recv_instance.recv(timeout=self.sleeptime)
        if self.comm in ['CommBase', 'AsyncComm']:
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

    def test_purge(self, nrecv=1):
        r"""Test purging messages from the comm."""
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)
        # Purge recv while open
        if self.comm not in ['CommBase', 'AsyncComm']:
            flag = self.send_instance.send(self.msg_short)
            assert(flag)
            T = self.recv_instance.start_timeout()
            while ((not T.is_out) and
                   (self.recv_instance.n_msg != nrecv)):  # pragma: debug
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

    def test_send_recv_dict(self):
        r"""Test send/recv message as dict."""
        msg_send = dict(f0=self.map_sent2recv(self.msg_short))
        self.do_send_recv(send_meth='send_dict', recv_meth='recv_dict',
                          msg_send=msg_send)
