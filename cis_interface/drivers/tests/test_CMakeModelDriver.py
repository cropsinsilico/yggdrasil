import os
import nose.tools as nt
import unittest
from cis_interface import tools
from cis_interface.tests import scripts
import cis_interface.drivers.tests.test_ModelDriver as parent
from cis_interface.drivers.CMakeModelDriver import (
    CMakeModelDriver, create_include)


def test_create_include():
    r"""Test create_include."""
    target = 'target'
    testlist = [(['-DCIS'], [], ['ADD_DEFINITIONS(-DCIS)']),
                (['-Iinclude_dir'], [], ['INCLUDE_DIRECTORIES(include_dir)']),
                ([], ['-lm'], ['TARGET_LINK_LIBRARIES(%s -lm)' % target]),
                ([], ['-Llib_dir'], ['LINK_DIRECTORIES(lib_dir)']),
                ([], ['/LIBPATH:"lib_dir"'], ['LINK_DIRECTORIES(lib_dir)']),
                ([], ['m'], ['TARGET_LINK_LIBRARIES(%s m)' % target])]
    for c, l, lines in testlist:
        out = create_include(None, target, compile_flags=c,
                             linker_flags=l)
        for x in lines:
            print(x, out)
            assert(x in out)
    nt.assert_raises(ValueError, create_include,
                     None, target, compile_flags=['invalid'])
    nt.assert_raises(ValueError, create_include,
                     None, target, linker_flags=['-invalid'])
    nt.assert_raises(ValueError, create_include,
                     None, target, linker_flags=['/invalid'])


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
                           'builddir', 'target_file', 'include_file',
                           'cmakeargs']
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
