import uuid
import copy
import nose.tools as nt
from cis_interface.tests import MagicTestError
from cis_interface.drivers import import_driver
from cis_interface.drivers.tests import test_Driver as parent
from cis_interface import tools
from cis_interface.communication import (
    get_comm_class, new_comm)

            
class TestCommParam(parent.TestParam):
    r"""Test parameters for the CommDriver class."""
    def __init__(self, *args, **kwargs):
        super(TestCommParam, self).__init__(*args, **kwargs)
        self.driver = 'CommDriver'
        self.comm_name = tools.get_default_comm()
        self.attr_list += ['state', 'numSent', 'numReceived', 'comm_name',
                           'comm']
        # self.timeout = 1.0
        self._extra_instances = []

    @property
    def maxMsgSize(self):
        r"""int: Maximum message size."""
        return self.instance.maxMsgSize

    @property
    def is_input(self):
        r"""bool: True if the driver is for input, False otherwise."""
        return ('Input' in self.driver)
    
    @property
    def send_comm(self):
        r"""Communicator for sending."""
        if self.is_input:
            return self.instance.comm
        else:
            return self.alt_comm

    @property
    def recv_comm(self):
        r"""Communicator for receiving."""
        if self.is_input:
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
        if self.is_input:
            out.update(**self.send_comm_kwargs)
        else:
            out.update(**self.recv_comm_kwargs)
        return out

    @property
    def alt_comm_kwargs(self):
        r"""dict: Keyword arguments for opposite comm."""
        if self.is_input:
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
        if not self.is_input:
            self.alt_comm = new_comm(self.name, dont_open=self.skip_start,
                                     **self.alt_comm_kwargs)
        super(TestCommParam, self).setup(*args, **kwargs)
        # If driver sending, create recv comm second
        if self.is_input:
            self.alt_comm = new_comm(self.name, dont_open=self.skip_start,
                                     **self.alt_comm_kwargs)

    def teardown(self, *args, **kwargs):
        r"""Destroy comm object pair."""
        # kwargs['ncurr_comm'] = self.comm_count
        self.alt_comm.close()
        assert(self.alt_comm.is_closed)
        super(TestCommParam, self).teardown(*args, **kwargs)
    

class TestCommDriverNoStart(TestCommParam, parent.TestDriverNoStart):
    r"""Test class for the CommDriver class without start."""

    def test_send_recv(self):
        r"""Test sending/receiving with queues closed."""
        self.send_comm.close()
        self.recv_comm.close()
        self.instance.close_comm()
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

    def get_fresh_name(self):
        r"""Get a fresh name for a new instance that won't overlap with the base."""
        return 'Test%s_%s' % (self.cls, str(uuid.uuid4()))

    def get_fresh_error_instance(self):
        r"""Get CommDriver instance with an ErrorComm parent class."""
        args = [self.get_fresh_name()]
        if self.args is not None:
            args.append(copy.deepcopy(self.args))
        # args = self.inst_args
        kwargs = copy.deepcopy(self.inst_kwargs)
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
        # if not self.is_input:
        inst = self.get_fresh_error_instance()
        inst.comm.error_replace('n_msg')
        nt.assert_raises(MagicTestError, inst.stop)
        inst.comm.restore_all()
        inst.close_comm()
        assert(inst.is_comm_closed)
        

class TestCommDriver(TestCommParam, parent.TestDriver):
    r"""Test class for the CommDriver class."""

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
        if self.is_input:
            recv_mech = self.recv_comm
            send_mech = self.instance
        else:
            recv_mech = self.instance
            send_mech = self.send_comm
        flag = send_mech.send(self.msg_short)
        if self.comm_name != 'CommBase':
            assert(flag)
            T = self.instance.start_timeout()
            while (not T.is_out) and (recv_mech.n_msg == 0):  # pragma: debug
                self.instance.sleep()
            self.instance.stop_timeout()
            nt.assert_equal(recv_mech.n_msg, 1)
        flag, msg_recv = recv_mech.recv()
        if self.comm_name != 'CommBase':
            assert(flag)
            nt.assert_equal(msg_recv, self.msg_short)
            nt.assert_equal(recv_mech.n_msg, 0)

    def test_send_recv_nolimit(self):
        r"""Test sending/receiving large message."""
        assert(len(self.msg_long) > self.maxMsgSize)
        if self.is_input:
            recv_mech = self.recv_comm
            send_mech = self.instance
        else:
            recv_mech = self.instance
            send_mech = self.send_comm
        flag = send_mech.send_nolimit(self.msg_long)
        if self.comm_name != 'CommBase':
            assert(flag)
            T = self.instance.start_timeout()
            while (not T.is_out) and (recv_mech.n_msg == 0):  # pragma: debug
                self.instance.sleep()
            self.instance.stop_timeout()
            assert(recv_mech.n_msg > 0)
        flag, msg_recv = recv_mech.recv_nolimit()
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
