import importlib
import nose.tools as nt
from cis_interface.drivers.tests.test_IODriver import IOInfo
from cis_interface.drivers.tests import test_Driver as parent

            
class TestCommParam(parent.TestParam, IOInfo):
    r"""Test parameters for the CommDriver class.

    Attributes (in addition to parent class's):
        -

    """
    def __init__(self, *args, **kwargs):
        super(TestCommParam, self).__init__(*args, **kwargs)
        IOInfo.__init__(self)
        self.driver = 'CommDriver'
        self.comm_name = 'IPCComm'  # 'CommBase'
        self.attr_list += ['state', 'numSent', 'numReceived', 'comm_cls',
                           'comm']
        self.timeout = 1.0
    
    @property
    def send_comm(self):
        r"""Communicator for sending."""
        if 'Input' in self.driver:
            return self.instance.comm
        else:
            return self.alt_comm

    @property
    def recv_comm(self):
        r"""Communicator for receiving."""
        if 'Input' in self.driver:
            return self.alt_comm
        else:
            return self.instance.comm

    @property
    def send_comm_kwargs(self):
        r"""dict: Keyword arguments for send comm."""
        return {'timeout': self.timeout}

    @property
    def recv_comm_kwargs(self):
        r"""dict: Keyword arguments for recv comm."""
        return self.send_comm.opp_comm_kwargs()
    
    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for tested class."""
        out = super(TestCommParam, self).inst_kwargs
        del out['namespace'], out['yml']
        if 'Input' in self.driver:
            out.update(**self.send_comm_kwargs)
        else:
            out.update(**self.recv_comm_kwargs)
        out['comm'] = self.comm_name
        return out

    @property
    def alt_comm_kwargs(self):
        r"""dict: Keyword arguments for opposite comm."""
        if 'Input' in self.driver:
            out = self.recv_comm_kwargs
        else:
            out = self.send_comm_kwargs
        return out

    @property
    def comm_cls(self):
        r"""Comm class."""
        comm_mod = importlib.import_module('cis_interface.communication.%s' %
                                           self.comm_name)
        comm_cls = getattr(comm_mod, self.comm_name)
        return comm_cls

    def setup(self, *args, **kwargs):
        r"""Initialize comm object pair."""
        comm_cls = self.comm_cls
        kwargs['nprev_queues'] = comm_cls.comm_count
        # If driver receiving, create send comm first
        if 'Input' not in self.driver:
            self.alt_comm = comm_cls.new_comm(self.name, **self.alt_comm_kwargs)
        super(TestCommParam, self).setup(*args, **kwargs)
        # If driver sending, create recv comm second
        if 'Input' in self.driver:
            self.alt_comm = comm_cls.new_comm(self.name, **self.alt_comm_kwargs)

    def teardown(self, *args, **kwargs):
        r"""Destroy comm object pair."""
        kwargs['ncurr_queues'] = self.comm_cls.comm_count
        self.alt_comm.close()
        assert(self.alt_comm.is_closed)
        super(TestCommParam, self).teardown(*args, **kwargs)
    

class TestCommDriverNoStart(TestCommParam, parent.TestDriverNoStart):
    r"""Test class for the CommDriver class without start.

    Attributes (in addition to parent class's):
        -

    """

    def test_send_recv(self):
        r"""Test sending/receiving with queues closed."""
        self.instance.close_comm()
        assert(not self.instance.is_comm_open)
        # Short
        flag = self.send_comm.send(self.msg_short)
        # assert(not flag)  # Send comm open
        flag, ret = self.instance.recv()
        assert(not flag)
        nt.assert_equal(ret, None)
        # Long
        flag = self.send_comm.send_nolimit(self.msg_short)
        # assert(not flag)  # Send comm open
        flag, ret = self.instance.recv_nolimit()
        assert(not flag)
        nt.assert_equal(ret, None)


class TestCommDriver(TestCommParam, parent.TestDriver):
    r"""Test class for the CommDriver class.

    Attributes (in addition to parent class's):
        -

    """

    def setup(self, *args, **kwargs):
        r"""Initialize comm object pair."""
        super(TestCommDriver, self).setup(*args, **kwargs)
        # CommBase is dummy class that never opens
        if self.comm_name != 'CommBase':
            assert(self.send_comm.is_open)
            assert(self.recv_comm.is_open)

    def test_early_close(self):
        r"""Test early deletion of message queue."""
        self.instance.close_comm()

    def test_send_recv(self):
        r"""Test sending/receiving small message."""
        flag = self.send_comm.send(self.msg_short)
        if self.comm_name != 'CommBase':
            assert(flag)
        self.instance.sleep()
        if self.comm_name != 'CommBase':
            nt.assert_equal(self.instance.n_msg, 1)
        flag, msg_recv = self.instance.recv()
        if self.comm_name != 'CommBase':
            assert(flag)
            nt.assert_equal(msg_recv, self.msg_short)
            nt.assert_equal(self.instance.n_msg, 0)

    def test_send_recv_nolimit(self):
        r"""Test sending/receiving large message."""
        assert(len(self.msg_long) > self.maxMsgSize)
        flag = self.send_comm.send_nolimit(self.msg_long)
        if self.comm_name != 'CommBase':
            assert(flag)
        flag, msg_recv = self.instance.recv_nolimit()
        if self.comm_name != 'CommBase':
            assert(flag)
            nt.assert_equal(msg_recv, self.msg_long)

    def assert_before_stop(self):
        r"""Assertions to make before stopping the driver instance."""
        super(TestCommDriver, self).assert_before_stop()
        if self.comm_name != 'CommBase':
            assert(self.instance.is_comm_open)

    def run_before_terminate(self):
        r"""Commands to run while the instance is running, before terminate."""
        self.send_comm.send(self.msg_short)

    def assert_after_terminate(self):
        r"""Assertions to make after terminating the driver instance."""
        super(TestCommDriver, self).assert_after_terminate()
        assert(self.instance.is_comm_closed)
