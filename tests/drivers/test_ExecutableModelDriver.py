import unittest
from yggdrasil import platform
from yggdrasil.tests import assert_raises
from yggdrasil.drivers.ExecutableModelDriver import ExecutableModelDriver
import yggdrasil.drivers.tests.test_ModelDriver as parent


def test_execution_error():
    r"""Test errors raised during execution of invalid command."""
    assert_raises(RuntimeError, ExecutableModelDriver.run_executable,
                  ['invalid'])


def test_error_valgrind_strace():
    r"""Test error if both valgrind and strace set."""
    assert_raises(RuntimeError, ExecutableModelDriver, 'test', 'test',
                  with_strace=True, with_valgrind=True)


@unittest.skipIf(not platform._is_win, "Platform is not windows")
def test_error_valgrind_strace_windows():  # pragma: windows
    r"""Test error if strace or valgrind called on windows."""
    assert_raises(RuntimeError, ExecutableModelDriver, 'test', 'test',
                  with_strace=True)
    assert_raises(RuntimeError, ExecutableModelDriver, 'test', 'test',
                  with_valgrind=True)

    
class TestExecutableModelParam(parent.TestModelParam):
    r"""Test parameters for ExecutableModelDriver class."""

    driver = 'ExecutableModelDriver'

            
class TestExecutableModelDriverNoInit(TestExecutableModelParam,
                                      parent.TestModelDriverNoInit):
    r"""Test runner for ExecutableModelDriver class without init."""
    pass


class TestExecutableModelDriverNoStart(TestExecutableModelParam,
                                       parent.TestModelDriverNoStart):
    r"""Test runner for ExecutableModelDriver class without start."""
    pass


class TestExecutableModelDriver(TestExecutableModelParam,
                                parent.TestModelDriver):
    r"""Test runner for ExecutableModelDriver class."""
    pass
