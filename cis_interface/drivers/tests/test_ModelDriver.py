import unittest
from cis_interface.tests import assert_raises
from cis_interface import platform
from cis_interface.drivers.ModelDriver import ModelDriver
import cis_interface.drivers.tests.test_Driver as parent


def test_error_valgrind_strace():
    r"""Test error if both valgrind and strace set."""
    assert_raises(RuntimeError, ModelDriver, 'test', 'test',
                  with_strace=True, with_valgrind=True)


@unittest.skipIf(not platform._is_win, "Platform is not windows")
def test_error_valgrind_strace_windows():  # pragma: windows
    r"""Test error if strace or valgrind called on windows."""
    assert_raises(RuntimeError, ModelDriver, 'test', 'test',
                  with_strace=True)
    assert_raises(RuntimeError, ModelDriver, 'test', 'test',
                  with_valgrind=True)


class TestModelParam(parent.TestParam):
    r"""Test parameters for basic ModelDriver class."""

    driver = 'ModelDriver'
    
    def __init__(self, *args, **kwargs):
        super(TestModelParam, self).__init__(*args, **kwargs)
        if self.args is None:
            if platform._is_win:  # pragma: windows
                self.args = ['timeout', '0']
            else:
                self.args = ['sleep', '0.1']
        self.attr_list += ['args', 'process', 'queue', 'queue_thread',
                           'is_server', 'client_of',
                           'event_process_kill_called',
                           'event_process_kill_complete',
                           'with_strace', 'strace_flags',
                           'with_valgrind', 'valgrind_flags',
                           'model_index']
        

class TestModelDriverNoStart(TestModelParam, parent.TestDriverNoStart):
    r"""Test runner for basic ModelDriver class."""

    def test_is_installed(self):
        r"""Assert that the tested model driver is installed."""
        if self.driver == 'ModelDriver':
            assert(not self.import_cls.is_installed())
        else:
            assert(self.import_cls.is_installed())


class TestModelDriver(TestModelParam, parent.TestDriver):
    r"""Test runner for basic ModelDriver class."""

    pass


@unittest.skipIf(platform._is_win, "Platform is windows")
class TestModelDriver_valgrind(TestModelDriver):
    r"""Test with valgrind."""

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for creating a class instance."""
        out = super(TestModelDriver_valgrind, self).inst_kwargs
        out['with_valgrind'] = True
        return out


@unittest.skipIf(platform._is_win, "Platform is windows")
class TestModelDriver_strace(TestModelDriver):
    r"""Test with strace."""

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for creating a class instance."""
        out = super(TestModelDriver_strace, self).inst_kwargs
        out['with_strace'] = True
        return out
