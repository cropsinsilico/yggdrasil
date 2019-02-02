import uuid
import unittest
from yggdrasil import tools, backwards
from yggdrasil.tests import MagicTestError, assert_raises
from yggdrasil.schema import get_schema
from yggdrasil.drivers import import_driver
from yggdrasil.drivers.tests import test_Driver as parent
from yggdrasil.drivers.ConnectionDriver import ConnectionDriver
from yggdrasil.communication import (
    new_comm, ZMQComm, IPCComm, RMQComm, get_comm_class)


_default_comm = tools.get_default_comm()
_zmq_installed = ZMQComm.ZMQComm.is_installed(language='python')
_ipc_installed = IPCComm.IPCComm.is_installed(language='python')
_rmq_server_running = RMQComm._rmq_server_running

            
class TestConnectionParam(parent.TestParam):
    r"""Test parameters for the ConnectionDriver class."""

    comm_name = _default_comm
    icomm_name = _default_comm
    ocomm_name = _default_comm
    testing_option_kws = {}
    driver = 'ConnectionDriver'
    
    def __init__(self, *args, **kwargs):
        super(TestConnectionParam, self).__init__(*args, **kwargs)
        self.attr_list += ['icomm_kws', 'ocomm_kws', 'icomm', 'ocomm',
                           'nrecv', 'nproc', 'nsent', 'state', 'translator']
        # self.timeout = 1.0
        self._extra_instances = []

    @property
    def description_prefix(self):
        r"""String prefix to prepend docstr test message with."""
        out = super(TestConnectionParam, self).description_prefix
        return '%s(%s, %s)' % (out, self.icomm_name, self.ocomm_name)

    @property
    def maxMsgSize(self):
        r"""int: Maximum message size."""
        return min(self.instance.icomm.maxMsgSize,
                   self.instance.ocomm.maxMsgSize)

    @property
    def is_input(self):
        r"""bool: True if the connection is for input."""
        return (self.icomm_name != self.comm_name)

    @property
    def is_output(self):
        r"""bool: True if the connection is for output."""
        return (self.ocomm_name != self.comm_name)
        
    def assert_msg_equal(self, x, y):
        r"""Assert that two messages are equivalent."""
        self.assert_equal(x, y)

    def get_options(self):
        r"""Get testing options."""
        if self.is_output:
            out = self.ocomm_import_cls.get_testing_options(
                **self.testing_option_kws)
        else:
            out = self.icomm_import_cls.get_testing_options(
                **self.testing_option_kws)
        return out
    
    @property
    def cleanup_comm_classes(self):
        r"""list: Comm classes that should be cleaned up following the test."""
        comms = set([self.comm_name, self.icomm_name, self.ocomm_name])
        return comms

    @property
    def icomm_kws(self):
        r"""dict: Keyword arguments for connection input comm."""
        out = {'name': self.icomm_name, 'comm': self.icomm_name}
        if self.is_input:
            out.update(self.testing_options['kwargs'])
        return out

    @property
    def ocomm_kws(self):
        r"""dict: Keyword arguments for connection output comm."""
        out = {'name': self.ocomm_name, 'comm': self.ocomm_name}
        if self.is_output:
            out.update(self.testing_options['kwargs'])
        return out

    @property
    def icomm_import_cls(self):
        r"""class: Class used for connection input comm."""
        return get_comm_class(self.icomm_name)

    @property
    def ocomm_import_cls(self):
        r"""class: Class used for connection output comm."""
        return get_comm_class(self.ocomm_name)

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
        out['icomm_kws'] = self.icomm_kws
        out['ocomm_kws'] = self.ocomm_kws
        return out

    @property
    def test_msg(self):
        r"""str: Test message that should be used for any send/recv tests."""
        return self.testing_options['msg']

    @property
    def msg_long(self):
        r"""str: Small test message for sending."""
        msg_short = self.test_msg
        if isinstance(msg_short, backwards.bytes_type):
            out = msg_short + (self.maxMsgSize * b'0')
        else:  # pragma: debug
            out = msg_short
        # return self.testing_options['msg_long']
        return out
    
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
        flag = self.send_comm.send(self.test_msg)
        assert(not flag)
        flag, ret = self.recv_comm.recv()
        assert(not flag)
        self.assert_equal(ret, None)
        # Long
        flag = self.send_comm.send_nolimit(self.test_msg)
        assert(not flag)
        flag, ret = self.recv_comm.recv_nolimit()
        assert(not flag)
        self.assert_equal(ret, None)

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
            self.assert_raises(MagicTestError, driver_class, *args, **kwargs)
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
        self.assert_raises(MagicTestError, inst.open_comm)
        assert(inst.icomm.is_closed)
        inst.icomm.restore_all()

    def test_error_close_icomm(self):
        r"""Test forwarding of error from close of icomm."""
        inst = self.get_fresh_error_instance('icomm')
        inst.open_comm()
        inst.icomm.error_replace('close')
        self.assert_raises(MagicTestError, inst.close_comm)
        assert(inst.ocomm.is_closed)
        inst.icomm.restore_all()
        inst.icomm.close()
        assert(inst.icomm.is_closed)
        
    def test_error_close_ocomm(self):
        r"""Test forwarding of error from close of ocomm."""
        inst = self.get_fresh_error_instance('ocomm')
        inst.open_comm()
        inst.ocomm.error_replace('close')
        self.assert_raises(MagicTestError, inst.close_comm)
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
        self.assert_raises(Exception, inst.start)
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
        flag = self.send_comm.send(self.test_msg)
        if self.comm_name != 'CommBase':
            assert(flag)
        # self.instance.sleep()
        # if self.comm_name != 'CommBase':
        #     self.assert_equal(self.recv_comm.n_msg, 1)
        for i in range(self.nmsg_recv):
            flag, msg_recv = self.recv_comm.recv(self.timeout)
            if self.comm_name != 'CommBase':
                assert(flag)
                self.assert_msg_equal(msg_recv, self.test_msg)
        if self.comm_name != 'CommBase':
            self.assert_equal(self.instance.n_msg, 0)

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
        # self.send_comm.send(self.test_msg)

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
        out['translator'] = direct_translate
        out['onexit'] = 'printStatus'
        return out


def test_ConnectionDriverOnexit_errors():
    r"""Test that errors are raised for invalid onexit."""
    assert_raises(ValueError, ConnectionDriver, 'test',
                  onexit='invalid')


def test_ConnectionDriverTranslate_errors():
    r"""Test that errors are raised for invalid translators."""
    assert(not hasattr(invalid_translate, '__call__'))
    assert_raises(ValueError, ConnectionDriver, 'test',
                  translator=invalid_translate)

    
# Dynamically create tests based on registered file classes
s = get_schema()
comm_types = list(s['comm'].schema_subtypes.keys())
for k in comm_types:
    if k == _default_comm:
        continue
    # Output
    ocls = type('Test%sOutputDriver' % k,
                (TestConnectionDriver, ), {'ocomm_name': k,
                                           'driver': 'OutputDriver',
                                           'args': 'test'})
    # Input
    icls = type('Test%sInputDriver' % k,
                (TestConnectionDriver, ), {'icomm_name': k,
                                           'driver': 'InputDriver',
                                           'args': 'test'})
    # Flags
    flag_func = None
    if k in ['RMQComm', 'RMQAsyncComm']:
        flag_func = unittest.skipIf(not _rmq_server_running,
                                    "RMQ Server not running")
    elif k in ['ZMQComm']:
        flag_func = unittest.skipIf(not _zmq_installed,
                                    "ZMQ library not installed")
    elif k in ['IPCComm']:
        flag_func = unittest.skipIf(not _ipc_installed,
                                    "IPC library not installed")
    if flag_func is not None:
        ocls = flag_func(ocls)
        icls = flag_func(icls)
    # Add class to globals
    globals()[ocls.__name__] = ocls
    globals()[icls.__name__] = icls
    del ocls, icls
