import nose.tools as nt
from cis_interface.tests import IOInfo, MagicTestError
from cis_interface.drivers import import_driver
from cis_interface.drivers.tests import test_Driver as parent
from cis_interface.communication import (
    get_comm_class, new_comm, _default_comm)

            
class TestCommParam(parent.TestParam, IOInfo):
    r"""Test parameters for the CommDriver class.

    Attributes (in addition to parent class's):
        -

    """
    def __init__(self, *args, **kwargs):
        super(TestCommParam, self).__init__(*args, **kwargs)
        IOInfo.__init__(self)
        self.driver = 'CommDriver'
        self.comm_name = _default_comm
        self.attr_list += ['state', 'numSent', 'numReceived', 'comm_name',
                           'comm']
        self.timeout = 1.0
        self._extra_instances = []
    
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
        return {'timeout': self.timeout, 'comm': self.comm_name}

    @property
    def recv_comm_kwargs(self):
        r"""dict: Keyword arguments for recv comm."""
        return self.send_comm.opp_comm_kwargs()
    
    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for tested class."""
        out = super(TestCommParam, self).inst_kwargs
        for k in ['namespace', 'yml']:
            if k in out:
                del out[k]
        if 'Input' in self.driver:
            out.update(**self.send_comm_kwargs)
        else:
            out.update(**self.recv_comm_kwargs)
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
        return get_comm_class(self.comm_name)

    @property
    def comm_count(self):
        r"""int: Return the number of comms."""
        return self.comm_cls.comm_count()

    def setup(self, *args, **kwargs):
        r"""Initialize comm object pair."""
        kwargs['nprev_comm'] = self.comm_count
        # If driver receiving, create send comm first
        if 'Input' not in self.driver:
            self.alt_comm = new_comm(self.name, **self.alt_comm_kwargs)
        super(TestCommParam, self).setup(*args, **kwargs)
        # If driver sending, create recv comm second
        if 'Input' in self.driver:
            self.alt_comm = new_comm(self.name, **self.alt_comm_kwargs)

    def teardown(self, *args, **kwargs):
        r"""Destroy comm object pair."""
        # kwargs['ncurr_comm'] = self.comm_count
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
        self.send_comm.close()
        self.recv_comm.close()
        # self.instance.close_comm()
        assert(not self.instance.is_comm_open)
        # Short
        flag = self.instance.send(self.msg_short)
        assert(not flag)
        flag, ret = self.instance.recv()
        assert(not flag)
        nt.assert_equal(ret, None)
        # Long
        flag = self.instance.send_nolimit(self.msg_short)
        assert(not flag)
        flag, ret = self.instance.recv_nolimit()
        assert(not flag)
        nt.assert_equal(ret, None)

    def get_fresh_error_instance(self):
        r"""Get CommDriver instance with an ErrorComm parent class."""
        args = self.inst_args
        kwargs = self.inst_kwargs
        if 'address' in kwargs:
            del kwargs['address']
        kwargs.update(
            base_comm=self.comm_name, new_comm_class='ErrorComm')
        driver_class = import_driver(self.driver)
        inst = driver_class(*args, **kwargs)
        self._extra_instances.append(inst)
        return inst

    def test_error_open_fails(self):
        r"""Test error raised when comm fails to open."""
        inst = self.get_fresh_error_instance()
        old_timeout = inst.timeout
        inst.comm.empty_replace('open')
        inst.timeout = inst.sleeptime / 2.0
        nt.assert_raises(Exception, inst.start)
        inst.comm.restore_all()
        inst.timeout = old_timeout
        inst.close_comm()
        assert(inst.is_comm_closed)

    def test_error_on_graceful_stop(self):
        r"""Test error raised during graceful stop."""
        inst = self.get_fresh_error_instance()
        inst.comm.error_replace('n_msg')
        nt.assert_raises(MagicTestError, inst.stop)
        inst.comm.restore_all()
        inst.close_comm()
        assert(inst.is_comm_closed)
        

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
        super(TestCommDriver, self).run_before_terminate()
        self.send_comm.send(self.msg_short)

    def run_before_stop(self):
        r"""Commands to run while the instance is running."""
        super(TestCommDriver, self).run_before_stop()
        self.send_comm.send(self.msg_short)
        self._old_timeout = self.instance.timeout
        self.instance.timeout = self.instance.sleeptime
        
    def assert_after_terminate(self):
        r"""Assertions to make after terminating the driver instance."""
        super(TestCommDriver, self).assert_after_terminate()
        assert(self.instance.is_comm_closed)

    def assert_after_stop(self):
        r"""Assertions to make after stopping the driver instance."""
        super(TestCommDriver, self).assert_after_stop()
        self.instance.timeout = self._old_timeout
