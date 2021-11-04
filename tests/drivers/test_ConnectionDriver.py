import pytest
import copy
from yggdrasil import tools, platform, constants
from yggdrasil.components import import_component
from yggdrasil.drivers.ConnectionDriver import ConnectionDriver
from yggdrasil.communication import new_comm, CommBase
from tests import timeout_decorator
from tests.drivers.test_Driver import TestDriver as base_class


_default_comm = tools.get_default_comm()


@pytest.mark.skipif(platform._is_win,
                    reason=("Temp skip connection tests on windows for "
                            "time's sake."))
@pytest.mark.suite("connections")
class TestConnectionDriver(base_class):
    r"""Test class for the ConnectionDriver class."""

    _component_type = 'connection'
    parametrize_commtype = [_default_comm]

    @pytest.fixture(scope="class")
    def component_subtype(self):
        r"""Subtype of component being tested."""
        return 'connection'

    @pytest.fixture(scope="class")
    def default_comm(self):
        r"""str: Name of the default communicator."""
        return _default_comm

    @pytest.fixture(scope="class")
    def commtype(self, request):
        r"""str: Name of the communicator being tested."""
        return request.param

    @pytest.fixture(scope="class")
    def icomm_name(self, default_comm):
        r"""str: Name of the input communicator being tested."""
        return default_comm
    
    @pytest.fixture(scope="class")
    def ocomm_name(self, default_comm):
        r"""str: Name of the output communicator being tested."""
        return default_comm

    @pytest.fixture(scope="class", autouse=True)
    def running_service_for_comms(self, icomm_name, ocomm_name,
                                  running_service):
        if 'rest' in [icomm_name, ocomm_name]:
            with running_service('flask') as cli:
                yield cli
        else:
            yield None
            
    @pytest.fixture
    def maxMsgSize(self, instance):
        r"""int: Maximum message size."""
        return min(instance.icomm.maxMsgSize,
                   instance.ocomm.maxMsgSize)

    @pytest.fixture(scope="class")
    def is_output(self, default_comm, ocomm_name):
        r"""bool: True if the connection is for output."""
        return (ocomm_name != default_comm)

    @pytest.fixture(scope="class")
    def test_msg(self, testing_options):
        r"""str: Test message that should be used for any send/recv tests."""
        return testing_options['msg']
        
    @pytest.fixture(scope="class")
    def nested_result(self, nested_approx):
        r"""Convert a sent object into a received one."""
        def nested_result_w(obj):
            return nested_approx(obj)
        return nested_result_w

    @pytest.fixture(scope="class")
    def testing_options(self, python_class, options, is_output,
                        icomm_python_class, ocomm_python_class):
        r"""Testing options."""
        if 'explicit_testing_options' in options:
            return copy.deepcopy(options['explicit_testing_options'])
        if is_output:
            out = ocomm_python_class.get_testing_options(**options)
        else:
            out = icomm_python_class.get_testing_options(**options)
        return out
    
    @pytest.fixture
    def inputs(self, icomm_name, testing_options, is_output):
        r"""list: List of keyword arguments for connection input comms."""
        out = [{'name': icomm_name, 'commtype': icomm_name}]
        if not is_output:
            out[0].update(testing_options['kwargs'])
        return out

    @pytest.fixture
    def outputs(self, ocomm_name, testing_options, is_output):
        r"""list: List of keyword arguments for connection output comms."""
        out = [{'name': ocomm_name, 'commtype': ocomm_name}]
        if is_output:
            out[0].update(testing_options['kwargs'])
        return out

    @pytest.fixture(scope="class")
    def icomm_python_class(self, icomm_name):
        r"""class: Class used for connection input comm."""
        return import_component('comm', icomm_name)

    @pytest.fixture(scope="class")
    def ocomm_python_class(self, ocomm_name):
        r"""class: Class used for connection output comm."""
        return import_component('comm', ocomm_name)

    @pytest.fixture
    def send_comm_kwargs(self, instance, icomm_name):
        r"""dict: Keyword arguments for send comm."""
        out = instance.icomm.opp_comm_kwargs()
        if icomm_name == 'value':
            out['direction'] = 'recv'
        return out

    @pytest.fixture
    def recv_comm_kwargs(self, instance):
        r"""dict: Keyword arguments for recv comm."""
        return instance.ocomm.opp_comm_kwargs()

    @pytest.fixture
    def instance_kwargs(self, testing_options, timeout, working_dir,
                        polling_interval, namespace, inputs, outputs,
                        icomm_name, icomm_python_class,
                        ocomm_name, ocomm_python_class):
        r"""Keyword arguments for a new instance of the tested class."""
        if not (ocomm_python_class.is_installed(language='python')
                and icomm_python_class.is_installed(language='python')):
            pytest.skip(
                f"one of the tested comms ({icomm_name}="
                f"{icomm_python_class.is_installed(language='python')}, "
                f"{ocomm_name}="
                f"{ocomm_python_class.is_installed(language='python')}) "
                f"is not installed")
        return dict(testing_options.get('kwargs', {}),
                    yml={'working_dir': working_dir},
                    timeout=timeout, sleeptime=polling_interval,
                    namespace=namespace, inputs=inputs, outputs=outputs)

    @pytest.fixture
    def msg_long(self, test_msg, maxMsgSize):
        r"""str: Small test message for sending."""
        if isinstance(test_msg, bytes):
            out = test_msg + (maxMsgSize * b'0')
        else:  # pragma: debug
            out = test_msg
        return out

    @pytest.fixture
    def send_comm(self, name, send_comm_kwargs, close_comm):
        r"""CommBase: communicator for sending messages to the driver."""
        out = new_comm(name, **send_comm_kwargs)
        try:
            yield out
        finally:
            close_comm(out)
    
    @pytest.fixture
    def recv_comm(self, name, recv_comm_kwargs, close_comm):
        r"""CommBase: communicator for receiving messages from the driver."""
        out = new_comm(name, **recv_comm_kwargs)
        try:
            yield out
        finally:
            close_comm(out)
    
    def test_manipulate_shared_event(self, instance):
        r"""Test setting and clearing events in the shared dictionary."""
        instance.set_flag_attr('_skip_after_loop')
        assert(instance.check_flag_attr('_skip_after_loop'))
        instance.clear_flag_attr('_skip_after_loop')
        assert(not instance.check_flag_attr('_skip_after_loop'))

    def test_send_recv_closed(self, instance, send_comm, recv_comm, test_msg):
        r"""Test sending/receiving with queues closed."""
        instance.close_comm()
        send_comm.close()
        recv_comm.close()
        assert(instance.is_comm_closed)
        assert(send_comm.is_closed)
        assert(recv_comm.is_closed)
        flag = instance.send_message(CommBase.CommMessage(args=test_msg))
        assert(not flag)
        flag = instance.recv_message()
        if instance.icomm._commtype != 'value':
            assert(not flag)
        # Short
        if instance.icomm._commtype != 'value':
            flag = send_comm.send(test_msg)
            assert(not flag)
        flag, ret = recv_comm.recv()
        if instance.icomm._commtype != 'value':
            assert(not flag)
            assert(ret is None)
        # Long
        if instance.icomm._commtype != 'value':
            flag = send_comm.send_nolimit(test_msg)
            assert(not flag)
        flag, ret = recv_comm.recv_nolimit()
        if instance.icomm._commtype != 'value':
            assert(not flag)
            assert(ret is None)
        instance.confirm_output(timeout=1.0)

    def test_error_init_ocomm(self, monkeypatch, python_class,
                              instance_args, instance_kwargs,
                              MagicTestError):
        r"""Test forwarding of error from init of ocomm."""
        orig = python_class._init_single_comm

        def error_init_single_comm(self, direction, *args):
            if direction == 'output':
                x = MagicTestError()
                x.instance = self
                raise x
            else:
                return orig(self, direction, *args)
        with monkeypatch.context() as m:
            m.setattr(python_class, '_init_single_comm',
                      error_init_single_comm)
            with pytest.raises(MagicTestError) as excinfo:
                python_class(*instance_args, **instance_kwargs)
            excinfo.value.instance.disconnect()

    def test_error_open_icomm(self, monkeypatch, instance,
                              MagicTestError, magic_error_replacement):
        r"""Test fowarding of error from open of icomm."""
        with monkeypatch.context() as m:
            if hasattr(instance.icomm, '_wrapped'):
                m.setattr(instance.icomm._wrapped, 'open',
                          magic_error_replacement)
            else:
                m.setattr(instance.icomm, 'open', magic_error_replacement)
            with pytest.raises(MagicTestError):
                instance.open_comm()
            assert(instance.icomm.is_closed)

    def test_error_close_icomm(self, monkeypatch, instance,
                               MagicTestError, magic_error_replacement):
        r"""Test forwarding of error from close of icomm."""
        instance.open_comm()
        with monkeypatch.context() as m:
            if hasattr(instance.icomm, '_wrapped'):
                m.setattr(instance.icomm._wrapped, '_close',
                          magic_error_replacement)
            else:
                m.setattr(instance.icomm, 'close',
                          magic_error_replacement)
            with pytest.raises(MagicTestError):
                instance.close_comm()
        assert(instance.ocomm.is_closed)
        instance.icomm.close()
        assert(instance.icomm.is_closed)
        
    def test_error_close_ocomm(self, monkeypatch, instance,
                               MagicTestError, magic_error_replacement):
        r"""Test forwarding of error from close of ocomm."""
        instance.open_comm()
        with monkeypatch.context() as m:
            m.setattr(instance.ocomm, '_close',
                      magic_error_replacement)
            with pytest.raises(MagicTestError):
                instance.close_comm()
        assert(instance.icomm.is_closed)
        instance.ocomm.close()
        assert(instance.ocomm.is_closed)

    def test_error_open_fails(self, monkeypatch, instance):
        r"""Test error raised when comms fail to open."""
        def empty_open(*args, **kwargs):
            pass
        with monkeypatch.context() as m:
            def replace_open(x):
                if hasattr(x, '_wrapped'):
                    replace_open(x._wrapped)
                elif x._commtype.startswith('rmq'):
                    x.close()
                else:
                    m.setattr(x, 'open', empty_open)
            replace_open(instance.icomm)
            replace_open(instance.ocomm)
            m.setattr(instance, 'timeout', instance.sleeptime / 2.0)
            with pytest.raises(Exception):
                instance.start()
        instance.close_comm()
        assert(instance.is_comm_closed)

    @pytest.fixture
    def nmsg_recv(self, icomm_name, testing_options):
        r"""Expected number of messages."""
        if icomm_name == 'value':
            return testing_options['kwargs']['count']
        return 1

    @pytest.fixture
    def before_instance_started(self, send_comm, recv_comm):
        r"""Actions performed after teh instance is created, but before it
        is started."""
        def before_instance_started_w(x):
            pass
        return before_instance_started_w
    
    @pytest.fixture
    def after_instance_started(self, wait_on_function, recv_comm):
        r"""Action taken after the instance is started, but before tests
        begin."""
        def after_instance_started_w(instance):
            wait_on_function(lambda: instance.is_valid)
            recv_comm.drain_server_signon_messages()
        return after_instance_started_w
        
    def test_init_del(self, started_instance):
        r"""Test driver creation and deletion."""
        started_instance.printStatus(verbose=True)
        started_instance.printStatus(verbose=True, return_str=True)

    def test_early_close(self, started_instance):
        r"""Test early deletion of message queue."""
        started_instance.close_comm()
        started_instance.open_comm()
        assert(started_instance.is_comm_closed)

    @timeout_decorator(timeout=600)
    def test_send_recv(self, started_instance, send_comm, recv_comm,
                       test_msg, nmsg_recv, timeout, icomm_name,
                       nested_result):
        r"""Test sending/receiving small message."""
        try:
            if started_instance.icomm._commtype != 'value':
                flag = send_comm.send(test_msg)
                assert(flag)
            # started_instance.sleep()
            # assert(recv_comm.n_msg == 1)
            for i in range(nmsg_recv):
                flag, msg_recv = recv_comm.recv(timeout=timeout)
                assert(flag)
                assert(msg_recv == nested_result(test_msg))
            if icomm_name != 'value':
                assert(started_instance.n_msg == 0)
        except BaseException:  # pragma: debug
            send_comm.printStatus()
            started_instance.printStatus(verbose=True)
            recv_comm.printStatus()
            raise

    @timeout_decorator(timeout=600)
    def test_send_recv_nolimit(self, started_instance, send_comm, recv_comm,
                               msg_long, maxMsgSize, nmsg_recv, timeout,
                               nested_result):
        r"""Test sending/receiving large message."""
        try:
            if started_instance.icomm._commtype != 'value':
                assert(len(msg_long) > maxMsgSize)
                flag = send_comm.send_nolimit(msg_long)
                assert(flag)
            for i in range(nmsg_recv):
                flag, msg_recv = recv_comm.recv_nolimit(timeout=timeout)
                assert(flag)
                assert(msg_recv == nested_result(msg_long))
        except BaseException:  # pragma: debug
            send_comm.printStatus()
            started_instance.printStatus(verbose=True)
            recv_comm.printStatus()
            raise

    @pytest.fixture
    def assert_before_stop(self, icomm_name, instance):
        r"""Assertions to make before stopping the driver instance."""
        def assert_before_stop_w():
            if icomm_name != 'value':
                assert(instance.is_comm_open)
        return assert_before_stop_w

    # TODO: This fails with ZMQ
    # @pytest.fixture
    # def run_before_terminate(self, send_comm, test_msg):
    #     r"""Commands to run while the instance is running, before terminate."""
    #     def run_before_terminate_w():
    #         send_comm.send(test_msg)
    #     return run_before_terminate_w

    @pytest.fixture
    def assert_after_terminate(self, started_instance):
        r"""Assertions to make after terminating the driver instance."""
        def assert_after_terminate_w():
            assert(not started_instance.is_alive())
            assert(started_instance.is_comm_closed)
        return assert_after_terminate_w


class TestConnectionDriverFork(TestConnectionDriver):
    r"""Test class for the ConnectionDriver class between fork comms."""

    @pytest.fixture(scope="class")
    def ncomm_input(self):
        r"""int: Number of input comms."""
        return 2

    @pytest.fixture(scope="class")
    def ncomm_output(self):
        r"""int: Number of output comms."""
        return 1

    @pytest.fixture(scope="class")
    def nmsg_recv(self, ncomm_input, ncomm_output):
        r"""int: Number of messages expected."""
        return ncomm_input * ncomm_output

    @pytest.fixture
    def inputs(self, ncomm_input):
        r"""list: List of keyword arguments for connection input comms."""
        return [None for _ in range(ncomm_input)]


invalid_translate = True


class TestConnectionDriverTranslate(TestConnectionDriver):
    r"""Test class for the ConnectionDriver class with translator."""

    test_send_recv_nolimit = None

    @pytest.fixture
    def instance_kwargs(self, testing_options, timeout, working_dir,
                        polling_interval, namespace, inputs, outputs):
        r"""Keyword arguments for a new instance of the tested class."""
        return dict(testing_options.get('kwargs', {}),
                    yml={'working_dir': working_dir},
                    timeout=timeout, sleeptime=polling_interval,
                    namespace=namespace, inputs=inputs, outputs=outputs,
                    translator={'transformtype': 'select_fields',
                                'selected': ['a'],
                                'single_as_scalar': True},
                    onexit='printStatus')

    @pytest.fixture(scope="class")
    def test_msg(self):
        r"""str: Test message that should be used for any send/recv tests."""
        return {'a': int(1), 'b': float(2)}

    @pytest.fixture(scope="class")
    def nested_result(self, nested_approx):
        r"""Convert a sent object into a received one."""
        def nested_result_w(obj):
            return nested_approx(obj['a'])
        return nested_result_w
    

class TestConnectionDriverIterate(TestConnectionDriver):
    r"""Test class for the ConnectionDriver class with iteration."""

    test_send_recv_nolimit = None

    @pytest.fixture
    def instance_kwargs(self, testing_options, timeout, working_dir,
                        polling_interval, namespace, inputs, outputs):
        r"""Keyword arguments for a new instance of the tested class."""
        return dict(testing_options.get('kwargs', {}),
                    yml={'working_dir': working_dir},
                    timeout=timeout, sleeptime=polling_interval,
                    namespace=namespace, inputs=inputs, outputs=outputs,
                    translator=[{'transformtype': 'select_fields',
                                 'selected': ['a', 'b']},
                                {'transformtype': 'iterate'}],
                    onexit='printStatus')

    @pytest.fixture(scope="class")
    def test_msg(self):
        r"""str: Test message that should be used for any send/recv tests."""
        return {'a': int(1), 'b': 'hello', 'c': float(2)}

    @timeout_decorator(timeout=600)
    def test_send_recv(self, started_instance, send_comm, recv_comm, test_msg,
                       timeout, nested_result):
        r"""Test sending/receiving small message."""
        msg = test_msg
        flag = send_comm.send(msg)
        assert(flag)
        for imsg in [v for k, v in msg.items() if k in ['a', 'b']]:
            flag, msg_recv = recv_comm.recv(timeout)
            assert(flag)
            assert(msg_recv == nested_result(imsg))
        assert(started_instance.n_msg == 0)


class TestConnectionDriverProcess(TestConnectionDriver):
    r"""Test class for the TestConnectionDriver using process."""

    test_send_recv_closed = None

    @pytest.fixture(scope="class")
    def icomm_name(self):
        r"""str: Name of the input communicator being tested."""
        return 'buffer'
    
    @pytest.fixture
    def instance_kwargs(self, testing_options, timeout, working_dir,
                        polling_interval, namespace, inputs, outputs):
        r"""Keyword arguments for a new instance of the tested class."""
        return dict(testing_options.get('kwargs', {}),
                    yml={'working_dir': working_dir},
                    timeout=timeout, sleeptime=polling_interval,
                    namespace=namespace, inputs=inputs, outputs=outputs,
                    task_method='process')


def test_ConnectionDriverOnexit_errors():
    r"""Test that errors are raised for invalid onexit."""
    with pytest.raises(ValueError):
        ConnectionDriver('test', onexit='invalid')


def test_ConnectionDriverTranslate_errors():
    r"""Test that errors are raised for invalid translators."""
    assert(not hasattr(invalid_translate, '__call__'))
    with pytest.raises(ValueError):
        ConnectionDriver('test', translator=invalid_translate)


_comm_types = sorted(
    [x for x in constants.COMPONENT_REGISTRY['comm']['subtypes'].keys()
     if x not in [_default_comm, 'mpi']])


class TestOutputDriver(TestConnectionDriver):
    r"""Test output drivers for supported comm types."""

    parametrize_commtype = [x for x in _comm_types if x not in ['value']]

    @pytest.fixture(scope="class")
    def component_subtype(self):
        r"""Subtype of component being tested."""
        return 'output'
    
    @pytest.fixture
    def instance_args(self, name):
        r"""Arguments for a new instance of the tested class."""
        return (name, 'test')
    
    @pytest.fixture(scope="class")
    def ocomm_name(self, commtype):
        r"""str: Name of the output communicator being tested."""
        return commtype


class TestInputDriver(TestConnectionDriver):
    r"""Test input drivers for supported comm types."""

    parametrize_commtype = _comm_types

    @pytest.fixture(scope="class")
    def component_subtype(self):
        r"""Subtype of component being tested."""
        return 'input'
    
    @pytest.fixture
    def instance_args(self, name):
        r"""Arguments for a new instance of the tested class."""
        return (name, 'test')
    
    @pytest.fixture(scope="class")
    def icomm_name(self, commtype):
        r"""str: Name of the input communicator being tested."""
        return commtype
