import pytest
from yggdrasil import platform
from yggdrasil.drivers.ExecutableModelDriver import ExecutableModelDriver


def test_execution_error():
    r"""Test errors raised during execution of invalid command."""
    with pytest.raises(RuntimeError):
        ExecutableModelDriver.run_executable(['invalid'])


def test_error_valgrind_strace():
    r"""Test error if both valgrind and strace set."""
    with pytest.raises(RuntimeError):
        ExecutableModelDriver('test', 'test',
                              with_strace=True, with_valgrind=True)


@pytest.mark.skipif(not platform._is_win, reason="Platform is not windows")
def test_error_valgrind_strace_windows():  # pragma: windows
    r"""Test error if strace or valgrind called on windows."""
    with pytest.raises(RuntimeError):
        ExecutableModelDriver('test', 'test', with_strace=True)
    with pytest.raises(RuntimeError):
        ExecutableModelDriver('test', 'test', with_valgrind=True)
