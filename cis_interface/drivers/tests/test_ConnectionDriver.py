import nose.tools as nt
from cis_interface.drivers.tests.test_IODriver import IOInfo
from cis_interface.drivers.tests import test_Driver as parent
from cis_interface.communication import get_comm_class, new_comm, CommBase

            
class TestConnectionParam(parent.TestParam, IOInfo):
    r"""Test parameters for the ConnectionDriver class.

    Attributes (in addition to parent class's):
        -

    """
    def __init__(self, *args, **kwargs):
        super(TestConnectionParam, self).__init__(*args, **kwargs)
        IOInfo.__init__(self)
        self.driver = 'ConnectionDriver'
        self.comm_name = 'IPCComm'
        self.attr_list += ['icomm_kws', 'ocomm_kws', 'icomm', 'ocomm',
                           'nrecv', 'nproc', 'nsent', 'state']
        self.timeout = 1.0
        self.icomm_name = self.comm_name
        self.ocomm_name = self.comm_name
    
    @property
    def send_comm_kwargs(self):
        r"""dict: Keyword arguments for send comm."""
        return self.instance.icomm.opp_comm_kwargs()

    @property
    def recv_comm_kwargs(self):
        r"""dict: Keyword arguments for recv comm."""
        return self.instance.ocomm.opp_comm_kwargs()

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for tested class."""
        out = super(TestConnectionParam, self).inst_kwargs
        out['icomm_kws'] = {'comm': self.icomm_name}
        out['ocomm_kws'] = {'comm': self.ocomm_name}
        return out

    @property
    def comm_cls(self):
        r"""Connection class."""
        return get_comm_class(self.comm_name)

    def setup(self, *args, **kwargs):
        r"""Initialize comm object pair."""
        kwargs['nprev_queues'] = self.comm_cls.comm_count
        super(TestConnectionParam, self).setup(*args, **kwargs)
        send_kws = self.send_comm_kwargs
        recv_kws = self.recv_comm_kwargs
        if kwargs.get('skip_start', False):
            send_kws['dont_open'] = True
            recv_kws['dont_open'] = True
        self.send_comm = new_comm(self.name, **send_kws)
        self.recv_comm = new_comm(self.name, **recv_kws)

    def teardown(self, *args, **kwargs):
        r"""Destroy comm object pair."""
        kwargs['ncurr_queues'] = self.comm_cls.comm_count
        self.send_comm.close()
        self.recv_comm.close()
        assert(self.send_comm.is_closed)
        assert(self.recv_comm.is_closed)
        super(TestConnectionParam, self).teardown(*args, **kwargs)
    

class TestConnectionDriverNoStart(TestConnectionParam, parent.TestDriverNoStart):
    r"""Test class for the ConnectionDriver class without start.

    Attributes (in addition to parent class's):
        -

    """

    def setup(self, *args, **kwargs):
        r"""Create a driver instance without starting the driver."""
        kwargs['skip_start'] = True
        super(TestConnectionDriverNoStart, self).setup(*args, **kwargs)
        assert(not self.instance.is_alive())

    def test_send_recv(self):
        r"""Test sending/receiving with queues closed."""
        self.instance.close_comm()
        self.send_comm.close()
        self.recv_comm.close()
        assert(self.instance.is_comm_closed)
        # Short
        flag = self.send_comm.send(self.msg_short)
        assert(not flag)
        flag, ret = self.recv_comm.recv()
        assert(not flag)
        nt.assert_equal(ret, None)
        # Long
        flag = self.send_comm.send_nolimit(self.msg_short)
        assert(not flag)
        flag, ret = self.recv_comm.recv_nolimit()
        assert(not flag)
        nt.assert_equal(ret, None)


class TestConnectionDriver(TestConnectionParam, parent.TestDriver):
    r"""Test class for the ConnectionDriver class.

    Attributes (in addition to parent class's):
        -

    """

    def setup(self, *args, **kwargs):
        r"""Initialize comm object pair."""
        super(TestConnectionDriver, self).setup(*args, **kwargs)
        # CommBase is dummy class that never opens
        if not isinstance(self.send_comm, CommBase.CommBase):
            assert(self.send_comm.is_open)
        if not isinstance(self.recv_comm, CommBase.CommBase):
            assert(self.recv_comm.is_open)

    def test_early_close(self):
        r"""Test early deletion of message queue."""
        self.instance.close_comm()

    def test_send_recv(self):
        r"""Test sending/receiving small message."""
        flag = self.send_comm.send(self.msg_short)
        if self.comm_name != 'CommBase':
            assert(flag)
        # self.instance.sleep()
        # if self.comm_name != 'CommBase':
        #     nt.assert_equal(self.recv_comm.n_msg, 1)
        flag, msg_recv = self.recv_comm.recv(self.timeout)
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
        flag, msg_recv = self.recv_comm.recv_nolimit(self.timeout)
        if self.comm_name != 'CommBase':
            assert(flag)
            nt.assert_equal(msg_recv, self.msg_long)

    def assert_before_stop(self):
        r"""Assertions to make before stopping the driver instance."""
        super(TestConnectionDriver, self).assert_before_stop()
        if self.comm_name != 'CommBase':
            assert(self.instance.is_comm_open)

    def run_before_terminate(self):
        r"""Commands to run while the instance is running, before terminate."""
        self.send_comm.send(self.msg_short)

    def assert_after_terminate(self):
        r"""Assertions to make after terminating the driver instance."""
        super(TestConnectionDriver, self).assert_after_terminate()
        assert(self.instance.is_comm_closed)
