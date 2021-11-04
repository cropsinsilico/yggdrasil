import pytest
import pickle
from yggdrasil import multitasking
from tests import TestClassBase as base_class


class TstClass(object):
    
    x = 'test'


class LockedTstClass(multitasking.LockedObject):

    _base_class = TstClass
    _base_attr = ['x']


def test_LockedAttr():
    r"""Test access to locked attribute."""
    z = LockedTstClass()
    z.x
    z.disconnect()
    with pytest.raises(multitasking.AliasDisconnectError):
        z.x


def test_WaitableFunction():
    r"""Test WaitableFunction."""
    def always_false():
        return False
    x = multitasking.WaitableFunction(always_false, polling_interval=0.0)
    assert(not x.wait(timeout=0.0, on_timeout=True))
    with pytest.raises(multitasking.TimeoutError):
        x.wait(timeout=0.0, on_timeout="Error message")


def test_TaskThread():
    r"""Test thread based Task."""
    q = multitasking.Task(target=multitasking.test_target_error)
    assert(not q.is_alive())
    q.start()
    q._base._errored.wait(1.0)
    assert(q._base._errored.is_set())
    q.join(60.0)
    assert(not q.is_alive())


def test_TaskProcess():
    r"""Test process based Task."""
    q = multitasking.Task(target=multitasking.test_target_error,
                          task_method='parallel')
    assert(not q.is_alive())
    q.start()
    q.join(60.0)
    assert(not q.is_alive())


class TestContextThread(base_class):
    r"""Test for thread based Context."""

    _cls = 'Context'
    _mod = 'yggdrasil.multitasking'
    _task_method = 'thread'

    @pytest.fixture(scope="class", autouse=True)
    def reset_test(self, module_name, class_name, task_method):
        self.__class__._first_test = True

    @pytest.fixture(scope="class", autouse=True, params=['thread', 'process'])
    def task_method(self, request):
        r"""Method that should be used for the generatd task."""
        return request.param
    
    @pytest.fixture(scope="class")
    def instance_kwargs(self, task_method):
        r"""Keyword arguments for a new instance of the tested class."""
        return dict(task_method=task_method)
        
    def test_RLock(self, instance):
        r"""Test creation of RLock from context."""
        x = instance.RLock()
        x.disconnect()

    def test_Event(self, instance):
        r"""Test creation of Event from context."""
        x = instance.Event()
        x.disconnect()

    def test_Task(self, instance):
        r"""Test creation of Task from context."""
        x = instance.Task()
        x.disconnect()

    def test_Queue(self, instance):
        r"""Test creation of Queue from context."""
        x = instance.Queue()
        x.disconnect()


class TstContextObject(object):

    _cls = None
    _mod = 'yggdrasil.multitasking'

    @pytest.fixture
    def check_decoded(self):
        r"""Check that object was decoded correctly."""
        def check_decoded_w(decoded):
            pass
        return check_decoded_w

    def test_pickle(self, instance, check_decoded):
        r"""Test pickling and unpickling the object."""
        encoded = pickle.dumps(instance)
        decoded = pickle.loads(encoded)
        check_decoded(decoded)


class TestRLock(TstContextObject, base_class):

    _cls = 'RLock'


class TestEvent(TstContextObject, base_class):

    _cls = 'Event'

    @pytest.fixture
    def check_decoded(self, instance):
        r"""Check that object was decoded correctly."""
        def check_decoded_w(decoded):
            assert(decoded.is_set() == instance.is_set())
        return check_decoded_w

    def test_pickle(self, instance, check_decoded):
        r"""Test pickling and unpickling the object."""
        instance.set()
        super(TestEvent, self).test_pickle(instance, check_decoded)

    def test_callback(self, instance):
        r"""Test callabacks."""
        def set_callback():
            self.state = 'set'

        def clear_callback():
            self.state = 'clear'

        instance.add_callback(set_callback, trigger='set')
        instance.add_callback(clear_callback, trigger='clear')
        instance.set()
        assert(self.state == 'set')
        instance.clear()
        assert(self.state == 'clear')


class TestValueEvent(TestEvent):

    _cls = 'ValueEvent'

    def test_value(self, instance):
        r"""Test setting/clearning event value."""
        assert(instance.get() is None)
        instance.set('test')
        assert(instance.get() == 'test')
        instance.clear()
        assert(instance.get() is None)


class TestTask(TstContextObject, base_class):

    _cls = 'Task'

    @pytest.fixture
    def check_decoded(self, instance):
        r"""Check that object was decoded correctly."""
        def check_decoded_w(decoded):
            assert(decoded.name == instance.name)
            assert(decoded.daemon == instance.daemon)
        return check_decoded_w


class TestQueue(TstContextObject, base_class):

    _cls = 'Queue'

    def test_join(self, instance):
        r"""Test join."""
        instance.join()


class TestYggTask(base_class):
    r"""Test basic behavior of YggTask class."""

    _cls = 'YggTask'
    _mod = 'yggdrasil.multitasking'

    @pytest.fixture(scope="class", autouse=True)
    def reset_test(self, module_name, class_name, task_method):
        self.__class__._first_test = True

    @pytest.fixture(scope="class", autouse=True, params=['thread', 'process'])
    def task_method(self, request):
        r"""Method that should be used for the generatd task."""
        return request.param

    @pytest.fixture(scope="class", autouse=True)
    def context(self, task_method):
        if task_method == 'process':
            return multitasking.mp_ctx_spawn
    
    @pytest.fixture(scope="class")
    def instance_kwargs(self, timeout, polling_interval, task_method,
                        context):
        r"""Keyword arguments for a new instance of the tested class."""
        return dict(timeout=timeout, sleeptime=polling_interval,
                    target=multitasking.test_target_sleep,
                    task_method=task_method,
                    context=context)

    @pytest.fixture
    def namespace(self, uuid):
        r"""Test namespace."""
        return f'TESTING_{uuid}'

    @pytest.fixture
    def instance(self, python_class, instance_args, instance_kwargs):
        r"""New instance of the python class for testing."""
        out = python_class(*instance_args, **instance_kwargs)
        yield out
        # Must disconnect as calling 'del' dosn't trigger garbage collection
        # until after tests due to presence of a ref in pytest fixtures
        out.disconnect()
        
    def test_id(self, instance):
        r"""Test process ID and ident."""
        instance.pid
        instance.ident

    def test_daemon(self, instance):
        r"""Test process/thread daemon property."""
        instance.daemon

    def test_exitcode(self, instance):
        r"""Test process exitcode."""
        instance.exitcode

    def test_get_main_proc(self, instance):
        r"""Test get_main_proc."""
        instance.get_main_proc()

    def test_kill(self, instance, task_method):
        r"""Test kill."""
        if task_method == 'process':
            instance.start()
        instance.kill()
        instance.exitcode

    def test_flag_manipulation(self, instance):
        r"""Test flag manipulation."""
        instance.set_flag_attr('error_flag')
        assert(instance.check_flag_attr('error_flag'))
        instance.clear_flag_attr('error_flag')
        assert(not instance.check_flag_attr('error_flag'))


class TestYggProcessFork(TestYggTask):
    r"""Test basic behavior of YggTask for forked process."""

    @pytest.fixture(scope="class", autouse=True, params=['process'])
    def task_method(self, request):
        r"""Method that should be used for the generatd task."""
        return request.param
    
    @pytest.fixture(scope="class")
    def instance_kwargs(self, timeout, polling_interval, task_method):
        r"""Keyword arguments for a new instance of the tested class."""
        return dict(timeout=timeout, sleeptime=polling_interval,
                    target=multitasking.test_target_sleep,
                    task_method=task_method,
                    context=multitasking.mp_ctx)
