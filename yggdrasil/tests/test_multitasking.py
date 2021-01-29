import pickle
from yggdrasil import multitasking, tools
from yggdrasil.tests import assert_raises
from yggdrasil.tests.test_tools import YggTestClass


class TstClass(object):
    
    x = 'test'


class LockedTstClass(multitasking.LockedObject):

    _base_class = TstClass
    _base_attr = ['x']


def target():
    raise RuntimeError("Test error.")


def test_LockedAttr():
    r"""Test access to locked attribute."""
    z = LockedTstClass()
    z.x
    z.disconnect()
    assert_raises(multitasking.AliasDisconnectError,
                  getattr, z, 'x')


def test_TaskThread():
    r"""Test thread based Task."""
    q = multitasking.Task(target=target)
    assert(not q.is_alive())
    q.start()
    q._base._errored.wait(1.0)
    assert(q._base._errored.is_set())


def test_TaskProcess():
    r"""Test process based Task."""
    q = multitasking.Task(target=target, task_method='parallel')
    assert(not q.is_alive())
    q.start()
    q.join(60.0)
    assert(not q.is_alive())


class TestContextThread(YggTestClass):
    r"""Test for thread based Context."""

    _cls = 'Context'
    _mod = 'yggdrasil.multitasking'
    _task_method = 'thread'

    def __init__(self, *args, **kwargs):
        super(TestContextThread, self).__init__(*args, **kwargs)
        self._inst_kwargs = {'task_method': self._task_method}

    def test_RLock(self):
        r"""Test creation of RLock from context."""
        x = self.instance.RLock()
        x.disconnect()

    def test_Event(self):
        r"""Test creation of Event from context."""
        x = self.instance.Event()
        x.disconnect()

    def test_Task(self):
        r"""Test creation of Task from context."""
        x = self.instance.Task()
        x.disconnect()

    def test_Queue(self):
        r"""Test creation of Queue from context."""
        x = self.instance.Queue()
        x.disconnect()


class TestContextProcess(YggTestClass):
    r"""Test for process based Context."""

    _task_method = 'process'


class TstContextObject(object):

    _cls = None
    _mod = 'yggdrasil.multitasking'

    def check_decoded(self, decoded):
        r"""Check that object was decoded correctly."""
        pass

    def test_pickle(self):
        r"""Test pickling and unpickling the object."""
        encoded = pickle.dumps(self.instance)
        decoded = pickle.loads(encoded)
        self.check_decoded(decoded)


class TestRLock(TstContextObject, YggTestClass):

    _cls = 'RLock'


class TestEvent(TstContextObject, YggTestClass):

    _cls = 'Event'

    def check_decoded(self, decoded):
        r"""Check that object was decoded correctly."""
        self.assert_equal(decoded.is_set(), self.instance.is_set())

    def test_pickle(self):
        r"""Test pickling and unpickling the object."""
        self.instance.set()
        super(TestEvent, self).test_pickle()


class TestTask(TstContextObject, YggTestClass):

    _cls = 'Task'

    def check_decoded(self, decoded):
        r"""Check that object was decoded correctly."""
        self.assert_equal(decoded.name, self.instance.name)
        self.assert_equal(decoded.daemon, self.instance.daemon)


class TestQueue(TstContextObject, YggTestClass):

    _cls = 'Queue'

    def test_join(self):
        r"""Test join."""
        self.instance.join()


class TestYggTask(YggTestClass):
    r"""Test basic behavior of YggTask class."""

    _cls = 'YggTask'
    _mod = 'yggdrasil.multitasking'

    def __init__(self, *args, **kwargs):
        super(TestYggTask, self).__init__(*args, **kwargs)
        self.namespace = 'TESTING_%s' % self.uuid
        self.attr_list += ['name', 'sleeptime', 'longsleep', 'timeout']
        self._inst_kwargs = {'timeout': self.timeout,
                             'sleeptime': self.sleeptime,
                             'target': self.target}
        self.debug_flag = False

    @staticmethod
    def target():  # pragma: no cover
        tools.sleep(10.0)

    def test_id(self):
        r"""Test process ID and ident."""
        self.instance.pid
        self.instance.ident

    def test_daemon(self):
        r"""Test process/thread daemon property."""
        self.instance.daemon

    def test_exitcode(self):
        r"""Test process exitcode."""
        self.instance.exitcode

    def test_get_main_proc(self):
        r"""Test get_main_proc."""
        self.instance.get_main_proc()

    def test_kill(self):
        r"""Test kill."""
        if self._inst_kwargs.get('task_method', None) == 'process':
            self.instance.start()
        self.instance.kill()
        self.instance.exitcode

    def test_flag_manipulation(self):
        r"""Test flag manipulation."""
        self.instance.set_flag_attr('error_flag')
        assert(self.instance.check_flag_attr('error_flag'))
        self.instance.clear_flag_attr('error_flag')
        assert(not self.instance.check_flag_attr('error_flag'))


class TestYggProcess(TestYggTask):
    r"""Test basic behavior of YggTask for spawned process."""

    def __init__(self, *args, **kwargs):
        super(TestYggProcess, self).__init__(*args, **kwargs)
        self._inst_kwargs['task_method'] = 'process'


class TestYggProcessFork(TestYggProcess):
    r"""Test basic behavior of YggTask for forked process."""

    def __init__(self, *args, **kwargs):
        super(TestYggProcessFork, self).__init__(*args, **kwargs)
        self._inst_kwargs['context'] = multitasking.mp_ctx
