import os
import nose.tools as nt
from cis_interface import platform
from cis_interface.tests import scripts
import cis_interface.drivers.tests.test_ModelDriver as parent
from cis_interface.drivers.GCCModelDriver import GCCModelDriver


def test_GCCModelDriver_errors():
    r"""Test GCCModelDriver errors."""
    nt.assert_raises(RuntimeError, GCCModelDriver, 'test', 'test.py')


class TestGCCModelParam(parent.TestModelParam):
    r"""Test parameters for GCCModelDriver."""

    def __init__(self, *args, **kwargs):
        super(TestGCCModelParam, self).__init__(*args, **kwargs)
        self.driver = 'GCCModelDriver'
        self.attr_list += []
        src = scripts['c']
        script_dir = os.path.dirname(src[0])
        if platform._is_win:
            self.args = src + ['1', '-I' + script_dir, '/link', '-L' + script_dir]
        else:
            self.args = src + ['1', '-I' + script_dir, '-L' + script_dir]

        
class TestGCCModelDriverNoStart(TestGCCModelParam,
                                parent.TestModelDriverNoStart):
    r"""Test runner for GCCModelDriver without start."""

    def __init__(self, *args, **kwargs):
        # Version to run C++ example
        super(TestGCCModelDriverNoStart, self).__init__(*args, **kwargs)
        src = scripts['cpp']
        script_dir = os.path.dirname(src[0])
        if platform._is_win:
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


class TestGCCModelDriverNoStart_std(TestGCCModelDriverNoStart):
    r"""Test runner for GCCModelDriver with std lib specified."""

    def __init__(self, *args, **kwargs):
        super(TestGCCModelDriverNoStart_std, self).__init__(*args, **kwargs)
        self.args.append('-std=c++11')


class TestGCCModelDriver(TestGCCModelParam, parent.TestModelDriver):
    r"""Test runner for GCCModelDriver."""

    pass
