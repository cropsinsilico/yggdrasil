from yggdrasil import multitasking
from yggdrasil.tests.test_tools import YggTestClass


class TestYggTask(YggTestClass):
    r"""Test basic behavior of YggTask class."""

    _cls = 'YggTask'
    _mod = 'yggdrasil.multitasking'

    def __init__(self, *args, **kwargs):
        super(TestYggTask, self).__init__(*args, **kwargs)
        self.namespace = 'TESTING_%s' % self.uuid
        self.attr_list += ['name', 'sleeptime', 'longsleep', 'timeout']
        self._inst_kwargs = {'timeout': self.timeout,
                             'sleeptime': self.sleeptime}
        self.debug_flag = False

    def test_id(self):
        r"""Test process ID and ident."""
        self.instance.pid
        self.instance.ident

    def test_exitcode(self):
        r"""Test process exitcode."""
        self.instance.exitcode

    def test_get_main_proc(self):
        r"""Test get_main_proc."""
        self.instance.get_main_proc()


class TestYggProcess(TestYggTask):
    r"""Test basic behavior of YggTask for spawned process."""

    def __init__(self, *args, **kwargs):
        super(TestYggProcess, self).__init__(*args, **kwargs)
        self._inst_kwargs['method'] = 'process'


class TestYggProcessFork(TestYggProcess):
    r"""Test basic behavior of YggTask for forked process."""

    def __init__(self, *args, **kwargs):
        super(TestYggProcessFork, self).__init__(*args, **kwargs)
        self._inst_kwargs['context'] = multitasking.mp_ctx
