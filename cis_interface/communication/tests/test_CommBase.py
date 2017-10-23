import nose.tools as nt
from cis_interface.tests import CisTest, IOInfo
from cis_interface.communication import new_comm


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
        return {'comm': self.comm}

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
    
    def setup(self, *args, **kwargs):
        r"""Initialize comm object pair."""
        self.send_instance = new_comm(self.name, **self.send_inst_kwargs)
        super(TestCommBase, self).setup(*args, **kwargs)
        # CommBase is dummy class that never opens
        if self.comm != 'CommBase':
            assert(self.send_instance.is_open)
            assert(self.recv_instance.is_open)

    def teardown(self, *args, **kwargs):
        r"""Destroy comm object pair."""
        self.remove_instance(self.send_instance)
        super(TestCommBase, self).teardown(*args, **kwargs)

    def remove_instance(self, inst):
        r"""Remove an instance."""
        inst.close()
        assert(inst.is_closed)
        super(TestCommBase, self).remove_instance(inst)

    def test_attributes(self):
        r"""Assert that the instance has all of the required attributes."""
        for a in self.attr_list:
            if not hasattr(self.instance, a):  # pragma: debug
                raise AttributeError("Driver does not have attribute %s" % a)

    def test_eof(self):
        r"""Test send/recv of EOF message."""
        if self.comm != 'CommBase':
            flag = self.send_instance.send(self.send_instance.eof_msg)
            assert(flag)
            flag, msg_recv = self.recv_instance.recv()
            assert(not flag)
            nt.assert_equal(msg_recv, self.send_instance.eof_msg)
            assert(self.recv_instance.is_closed)

    def test_eof_nolimit(self):
        r"""Test send/recv of EOF message through nolimit."""
        if self.comm != 'CommBase':
            flag = self.send_instance.send_nolimit(self.send_instance.eof_msg)
            assert(flag)
            flag, msg_recv = self.recv_instance.recv_nolimit()
            assert(not flag)
            nt.assert_equal(msg_recv, self.send_instance.eof_msg)
            assert(self.recv_instance.is_closed)

    def test_send_recv(self):
        r"""Test send/recv of a small message."""
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)
        if self.comm != 'CommBase':
            flag = self.send_instance.send(self.msg_short)
            assert(flag)
            nt.assert_equal(self.recv_instance.n_msg, 1)
            flag, msg_recv = self.recv_instance.recv()
            assert(flag)
            nt.assert_equal(msg_recv, self.msg_short)
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)

    def test_send_recv_nolimit(self):
        r"""Test send/recv of a large message."""
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)
        if self.comm != 'CommBase':
            assert(len(self.msg_long) > self.maxMsgSize)
            flag = self.send_instance.send_nolimit(self.msg_long)
            assert(flag)
            assert(self.recv_instance.n_msg >= 1)
            # IPC nolimit sends multiple messages
            # nt.assert_equal(self.recv_instance.n_msg, 1)
            flag, msg_recv = self.recv_instance.recv_nolimit()
            assert(flag)
            nt.assert_equal(msg_recv, self.msg_long)
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)

    def test_purge(self):
        r"""Test purging messages form the comm."""
        # Purge while open
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)
        if self.comm != 'CommBase':
            flag = self.send_instance.send(self.msg_short)
            assert(flag)
            nt.assert_equal(self.recv_instance.n_msg, 1)
        self.recv_instance.purge()
        nt.assert_equal(self.send_instance.n_msg, 0)
        nt.assert_equal(self.recv_instance.n_msg, 0)
        # Purge while closed
        self.recv_instance.close()
        self.recv_instance.purge()
