import uuid
import nose.tools as nt
from cis_interface import tools
from cis_interface.tests import MagicTestError
from cis_interface.drivers import import_driver
from cis_interface.drivers.tests import test_Driver as parent
from cis_interface.drivers.ConnectionDriver import ConnectionDriver
from cis_interface.communication import new_comm

            
class TestConnectionParam(parent.TestParam):
    r"""Test parameters for the ConnectionDriver class."""
    def __init__(self, *args, **kwargs):
        super(TestConnectionParam, self).__init__(*args, **kwargs)
        self.driver = 'ConnectionDriver'
        self.comm_name = tools.get_default_comm()
        self.attr_list += ['icomm_kws', 'ocomm_kws', 'icomm', 'ocomm',
                           'nrecv', 'nproc', 'nsent', 'state', 'translator']
        # self.timeout = 1.0
        self.icomm_name = self.comm_name
        self.ocomm_name = self.comm_name
        self._extra_instances = []

    def assert_msg_equal(self, x, y):
        r"""Assert that two messages are equal."""
        nt.assert_equal(x, y)
    
    @property
    def cleanup_comm_classes(self):
        r"""list: Comm classes that should be cleaned up following the test."""
        comms = set([self.comm_name, self.icomm_name, self.ocomm_name])
        return comms

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

    # @property
    # def comm_cls(self):
    #     r"""Connection class."""
    #     return get_comm_class(self.comm_name)

    def setup(self, *args, **kwargs):
        r"""Initialize comm object pair."""
        super(TestConnectionParam, self).setup(*args, **kwargs)
        send_kws = self.send_comm_kwargs
        recv_kws = self.recv_comm_kwargs
        if self.skip_start:
            send_kws['dont_open'] = True
            recv_kws['dont_open'] = True
        self.send_comm = new_comm(self.name, **send_kws)
        self.recv_comm = new_comm(self.name, **recv_kws)

    def teardown(self, *args, **kwargs):
        r"""Destroy comm object pair."""
        self.send_comm.close()
        self.recv_comm.close()
        assert(self.send_comm.is_closed)
        assert(self.recv_comm.is_closed)
        super(TestConnectionParam, self).teardown(*args, **kwargs)
        for inst in self._extra_instances:
            inst.terminate()
    

class TestConnectionDriverNoStart(TestConnectionParam, parent.TestDriverNoStart):
    r"""Test class for the ConnectionDriver class without start."""

    def test_send_recv(self):
        r"""Test sending/receiving with queues closed."""
        self.instance.close_comm()
        self.send_comm.close()
        self.recv_comm.close()
        assert(self.instance.is_comm_closed)
        assert(self.send_comm.is_closed)
        assert(self.recv_comm.is_closed)
        flag = self.instance.send_message()
        assert(not flag)
        flag = self.instance.recv_message()
        assert(not flag)
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

    def get_fresh_name(self):
        r"""Get a fresh name for a new instance that won't overlap with the base."""
        return 'Test%s_%s' % (self.cls, str(uuid.uuid4()))

    def get_fresh_error_instance(self, comm, error_on_init=False):
        r"""Get a driver instance with ErrorComm class for one or both comms."""
        args = [self.get_fresh_name()]
        if self.args is not None:
            args.append(self.args)
        # args = self.inst_args
        kwargs = self.inst_kwargs
        if 'comm_address' in kwargs:
            del kwargs['comm_address']
        if comm in ['ocomm', 'both']:
            kwargs['ocomm_kws'].update(
                base_comm=self.ocomm_name, new_comm_class='ErrorComm',
                error_on_init=error_on_init)
        if comm in ['icomm', 'both']:
            kwargs['icomm_kws'].update(
                base_comm=self.icomm_name, new_comm_class='ErrorComm',
                error_on_init=error_on_init)
        driver_class = import_driver(self.driver)
        if error_on_init:
            nt.assert_raises(MagicTestError, driver_class, *args, **kwargs)
        else:
            inst = driver_class(*args, **kwargs)
            inst.icomm._first_send_done = True
            self._extra_instances.append(inst)
            return inst

    def test_error_init_ocomm(self):
        r"""Test forwarding of error from init of ocomm."""
        self.get_fresh_error_instance('ocomm', error_on_init=True)

    def test_error_open_icomm(self):
        r"""Test fowarding of error from open of icomm."""
        inst = self.get_fresh_error_instance('icomm')
        inst.icomm.error_replace('open')
        nt.assert_raises(MagicTestError, inst.open_comm)
        assert(inst.icomm.is_closed)
        inst.icomm.restore_all()

    def test_error_close_icomm(self):
        r"""Test forwarding of error from close of icomm."""
        inst = self.get_fresh_error_instance('icomm')
        inst.open_comm()
        inst.icomm.error_replace('close')
        nt.assert_raises(MagicTestError, inst.close_comm)
        assert(inst.ocomm.is_closed)
        inst.icomm.restore_all()
        inst.icomm.close()
        assert(inst.icomm.is_closed)
        
    def test_error_close_ocomm(self):
        r"""Test forwarding of error from close of ocomm."""
        inst = self.get_fresh_error_instance('ocomm')
        inst.open_comm()
        inst.ocomm.error_replace('close')
        nt.assert_raises(MagicTestError, inst.close_comm)
        assert(inst.icomm.is_closed)
        inst.ocomm.restore_all()
        inst.ocomm.close()
        assert(inst.ocomm.is_closed)

    def test_error_open_fails(self):
        r"""Test error raised when comms fail to open."""
        inst = self.get_fresh_error_instance('both')
        old_timeout = inst.timeout
        inst.icomm.empty_replace('open')
        inst.ocomm.empty_replace('open')
        inst.timeout = inst.sleeptime / 2.0
        nt.assert_raises(Exception, inst.start)
        inst.timeout = old_timeout
        inst.icomm.restore_all()
        inst.ocomm.restore_all()
        inst.close_comm()
        assert(inst.is_comm_closed)


class TestConnectionDriver(TestConnectionParam, parent.TestDriver):
    r"""Test class for the ConnectionDriver class."""

    def setup(self, *args, **kwargs):
        r"""Initialize comm object pair."""
        super(TestConnectionDriver, self).setup(*args, **kwargs)
        # CommBase is dummy class that never opens
        if (self.send_comm.comm_class != 'CommBase'):
            assert(self.send_comm.is_open)
        if (self.recv_comm.comm_class != 'CommBase'):
            assert(self.recv_comm.is_open)
        self.nmsg_recv = 1

    def test_early_close(self):
        r"""Test early deletion of message queue."""
        self.instance.close_comm()
        self.instance.open_comm()
        assert(self.instance.is_comm_closed)

    def test_send_recv(self):
        r"""Test sending/receiving small message."""
        flag = self.send_comm.send(self.msg_short)
        if self.comm_name != 'CommBase':
            assert(flag)
        # self.instance.sleep()
        # if self.comm_name != 'CommBase':
        #     nt.assert_equal(self.recv_comm.n_msg, 1)
        for i in range(self.nmsg_recv):
            flag, msg_recv = self.recv_comm.recv(self.timeout)
            if self.comm_name != 'CommBase':
                assert(flag)
                self.assert_msg_equal(msg_recv, self.msg_short)
        if self.comm_name != 'CommBase':
            nt.assert_equal(self.instance.n_msg, 0)

    def test_send_recv_nolimit(self):
        r"""Test sending/receiving large message."""
        assert(len(self.msg_long) > self.maxMsgSize)
        flag = self.send_comm.send_nolimit(self.msg_long)
        if self.comm_name != 'CommBase':
            assert(flag)
        for i in range(self.nmsg_recv):
            flag, msg_recv = self.recv_comm.recv_nolimit(self.timeout)
            if self.comm_name != 'CommBase':
                assert(flag)
                self.assert_msg_equal(msg_recv, self.msg_long)

    def assert_before_stop(self, check_open=True):
        r"""Assertions to make before stopping the driver instance."""
        super(TestConnectionDriver, self).assert_before_stop()
        if self.comm_name != 'CommBase' and check_open:
            assert(self.instance.is_comm_open)

    def run_before_terminate(self):
        r"""Commands to run while the instance is running, before terminate."""
        super(TestConnectionDriver, self).run_before_terminate()
        # TODO: This fails with ZMQ
        # self.send_comm.send(self.msg_short)

    def assert_after_terminate(self):
        r"""Assertions to make after terminating the driver instance."""
        super(TestConnectionDriver, self).assert_after_terminate()
        assert(self.instance.is_comm_closed)


class TestConnectionDriverFork(TestConnectionDriver):
    r"""Test class for the ConnectionDriver class between fork comms."""

    def setup(self, *args, **kwargs):
        r"""Initialize comm object pair."""
        self.ncomm_input = 2
        self.ncomm_output = 1
        super(TestConnectionDriverFork, self).setup(*args, **kwargs)
        self.nmsg_recv = self.ncomm_input * self.ncomm_output

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for tested class."""
        out = super(TestConnectionDriverFork, self).inst_kwargs
        out['icomm_kws']['comm'] = [None for i in range(self.ncomm_input)]
        return out


def direct_translate(msg):
    r"""Test translator that just returns passed message."""
    return msg


invalid_translate = True


class TestConnectionDriverTranslate(TestConnectionDriver):
    r"""Test class for the ConnectionDriver class with translator."""

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for tested class."""
        out = super(TestConnectionDriverTranslate, self).inst_kwargs
        out['translator'] = '%s:direct_translate' % __name__
        out['onexit'] = 'printStatus'
        return out


def test_ConnectionDriverOnexit_errors():
    r"""Test that errors are raised for invalid onexit."""
    nt.assert_raises(ValueError, ConnectionDriver, 'test',
                     onexit='invalid')


def test_ConnectionDriverTranslate_errors():
    r"""Test that errors are raised for invalid translators."""
    nt.assert_raises(ValueError, ConnectionDriver, 'test',
                     translator='invalid:invalid:invalid')
    nt.assert_raises(AttributeError, ConnectionDriver, 'test',
                     translator='%s:noexist_translate' % __name__)
    assert(not hasattr(invalid_translate, '__call__'))
    nt.assert_raises(ValueError, ConnectionDriver, 'test',
                     translator='%s:invalid_translate' % __name__)
