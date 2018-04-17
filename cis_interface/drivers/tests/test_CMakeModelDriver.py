import os
import nose.tools as nt
import unittest
from cis_interface import tools
from cis_interface.tests import scripts
import cis_interface.drivers.tests.test_ModelDriver as parent
from cis_interface.drivers.CMakeModelDriver import CMakeModelDriver


@unittest.skipIf(tools._c_library_avail, "C Library installed")
def test_CMakeModelDriver_no_C_library():  # pragma: windows
    r"""Test CMakeModelDriver error when C library not installed."""
    nt.assert_raises(RuntimeError, CMakeModelDriver, 'test', scripts['cmake'])


@unittest.skipIf(not tools._c_library_avail, "C Library not installed")
def test_CMakeModelDriver_error_notarget():
    r"""Test CMakeModelDriver error for invalid target."""
    makedir, target = os.path.split(scripts['cmake'])
    nt.assert_raises(RuntimeError, CMakeModelDriver, 'test', 'invalid',
                     sourcedir=makedir)


@unittest.skipIf(not tools._c_library_avail, "C Library not installed")
def test_CMakeModelDriver_error_nofile():
    r"""Test CMakeModelDriver error for missing CMakeLists.txt."""
    makedir, target = os.path.split(scripts['cmake'])
    nt.assert_raises(IOError, CMakeModelDriver, 'test', 'invalid')


@unittest.skipIf(not tools._c_library_avail, "C Library not installed")
class TestCMakeModelParam(parent.TestModelParam):
    r"""Test parameters for CMakeModelDriver."""

    def __init__(self, *args, **kwargs):
        super(TestCMakeModelParam, self).__init__(*args, **kwargs)
        self.driver = 'CMakeModelDriver'
        self.attr_list += ['compiled', 'target', 'sourcedir',
                           'builddir', 'target_file', 'include_file']
        self.sourcedir, self.target = os.path.split(scripts['cmake'])
        self.args = [self.target]
        # self._inst_kwargs['yml']['workingDir']
        self._inst_kwargs['sourcedir'] = self.sourcedir
        

@unittest.skipIf(not tools._c_library_avail, "C Library not installed")
class TestCMakeModelDriverNoStart(TestCMakeModelParam,
                                  parent.TestModelDriverNoStart):
    r"""Test runner for CMakeModelDriver without start."""
    
    def __init__(self, *args, **kwargs):
        super(TestCMakeModelDriverNoStart, self).__init__(*args, **kwargs)
        # Version specifying sourcedir via workingDir
        self._inst_kwargs['yml']['workingDir'] = self.sourcedir
        self._inst_kwargs['sourcedir'] = None

    # Done in driver, but driver not started
    def teardown(self):
        r"""Remove the instance, stoppping it."""
        self.instance.cleanup()
        super(TestCMakeModelDriverNoStart, self).teardown()
        

@unittest.skipIf(not tools._c_library_avail, "C Library not installed")
class TestCMakeModelDriver(TestCMakeModelParam, parent.TestModelDriver):
    r"""Test runner for CMakeModelDriver."""
    pass
