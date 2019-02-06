import os
import unittest
from cis_interface import platform, tools
from cis_interface.tests import scripts, assert_equal, assert_raises
import cis_interface.drivers.tests.test_ModelDriver as parent
from cis_interface.drivers.GCCModelDriver import (
    GCCModelDriver, get_zmq_flags, get_ipc_flags, get_flags,
    build_datatypes, build_api, build_regex_win32)


_driver_installed = GCCModelDriver.is_installed()


def test_get_zmq_flags():
    r"""Test get_zmq_flags."""
    cc, ld = get_zmq_flags()
    if not tools.is_comm_installed('ZMQComm', language='c'):
        assert_equal(len(cc), 0)
        assert_equal(len(ld), 0)


def test_get_ipc_flags():
    r"""Test get_ipc_flags."""
    cc, ld = get_ipc_flags()
    if not tools.is_comm_installed('IPCComm', language='c'):  # pragma: windows
        assert_equal(len(cc), 0)
        assert_equal(len(ld), 0)


def test_get_flags():
    r"""Test get_flags."""
    cc, ld = get_flags()
    if not _driver_installed:  # pragma: windows
        assert_equal(len(cc), 0)
        assert_equal(len(ld), 0)


@unittest.skipIf(not _driver_installed, "C Library not installed")
def test_build_shared():
    r"""Test building libraries as shared."""
    if platform._is_win:  # pragma: windows
        build_regex_win32(overwrite=True)
    build_datatypes(as_shared=False, overwrite=True)
    build_datatypes(as_shared=True, overwrite=True)
    build_api(cpp=False, as_shared=True, overwrite=True)
    build_api(cpp=True, as_shared=True, overwrite=True)
    build_api(cpp=True, as_shared=True, overwrite=False)


@unittest.skipIf(_driver_installed, "C Library installed")
def test_GCCModelDriver_no_C_library():  # pragma: windows
    r"""Test GCCModelDriver error when C library not installed."""
    assert_raises(RuntimeError, GCCModelDriver, 'test', scripts['c'])


@unittest.skipIf(not _driver_installed, "C Library not installed")
def test_GCCModelDriver_errors():
    r"""Test GCCModelDriver errors."""
    assert_raises(RuntimeError, GCCModelDriver, 'test', 'test.py')


@unittest.skipIf(not _driver_installed, "C Library not installed")
class TestGCCModelParam(parent.TestModelParam):
    r"""Test parameters for GCCModelDriver."""

    driver = 'GCCModelDriver'
    
    def __init__(self, *args, **kwargs):
        super(TestGCCModelParam, self).__init__(*args, **kwargs)
        self.attr_list += []
        src = scripts['c']
        script_dir = os.path.dirname(src[0])
        if platform._is_win:  # pragma: windows
            self.args = src + ['1', '-I' + script_dir, '/link', '-L' + script_dir]
        else:
            self.args = src + ['1', '-I' + script_dir, '-L' + script_dir]


@unittest.skipIf(not _driver_installed, "C Library not installed")
class TestGCCModelDriverNoStart(TestGCCModelParam,
                                parent.TestModelDriverNoStart):
    r"""Test runner for GCCModelDriver without start."""

    def __init__(self, *args, **kwargs):
        # Version to run C++ example
        super(TestGCCModelDriverNoStart, self).__init__(*args, **kwargs)
        src = scripts['cpp']
        script_dir = os.path.dirname(src[0])
        if platform._is_win:  # pragma: windows
            self.args = src + ['1', '-I' + script_dir, '/link', '-L' + script_dir,
                               '/out:test_exe.exe']
        else:
            self.args = src + ['1', '-I' + script_dir, '-L' + script_dir,
                               '-o', 'test_exe']
    
    # Done in driver, but driver not started
    def teardown(self):
        r"""Remove the instance, stoppping it."""
        self.instance.cleanup()
        super(TestGCCModelDriverNoStart, self).teardown()


@unittest.skipIf(not _driver_installed, "C Library not installed")
class TestGCCModelDriverNoStart_std(TestGCCModelDriverNoStart):
    r"""Test runner for GCCModelDriver with std lib specified."""

    def __init__(self, *args, **kwargs):
        super(TestGCCModelDriverNoStart_std, self).__init__(*args, **kwargs)
        self.args.append('-std=c++11')


@unittest.skipIf(not _driver_installed, "C Library not installed")
class TestGCCModelDriver(TestGCCModelParam, parent.TestModelDriver):
    r"""Test runner for GCCModelDriver."""

    pass
