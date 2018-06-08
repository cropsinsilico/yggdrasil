import os
import nose.tools as nt
import unittest
import tempfile
from cis_interface import tools
from cis_interface.tests import scripts
import cis_interface.drivers.tests.test_ModelDriver as parent
from cis_interface.drivers.CMakeModelDriver import (
    CMakeModelDriver, create_include)


def test_create_include():
    r"""Test create_include."""
    target = 'target'
    tempdir = tempfile.gettempdir()
    fname_dll = os.path.join(tempdir, 'test.dll')
    fname_lib = os.path.join(tempdir, 'test.lib')
    for fname in [fname_dll, fname_lib]:
        with open(fname, 'w') as fd:
            fd.write('')
        assert(os.path.isfile(fname))
    testlist = [(['-DCIS'], [], ['ADD_DEFINITIONS(-DCIS)']),
                (['-Wall'], [], ['ADD_DEFINITIONS(-Wall)']),
                (['/nologo'], [], ['ADD_DEFINITIONS(/nologo)']),
                (['-Iinclude_dir'], [], ['INCLUDE_DIRECTORIES(include_dir)']),
                ([], ['-lm'], ['TARGET_LINK_LIBRARIES(%s -lm)' % target]),
                ([], ['-Llib_dir'], ['LINK_DIRECTORIES(lib_dir)']),
                ([], ['/LIBPATH:"lib_dir"'], ['LINK_DIRECTORIES(lib_dir)']),
                ([], ['m'], ['TARGET_LINK_LIBRARIES(%s m)' % target]),
                ([], [fname_dll], ['ADD_LIBRARY(test SHARED IMPORTED)']),
                ([], [fname_lib], ['ADD_LIBRARY(test STATIC IMPORTED)'])]
    for c, l, lines in testlist:
        out = create_include(None, target, compile_flags=c,
                             linker_flags=l)
        for x in lines:
            assert(x in out)
    for fname in [fname_dll, fname_lib]:
        os.remove(fname)
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
def test_CMakeModelDriver_error_cmake():
    r"""Test CMakeModelDriver error for invalid cmake args."""
    makedir, target = os.path.split(scripts['cmake'])
    nt.assert_raises(RuntimeError, CMakeModelDriver, 'test', target,
                     sourcedir=makedir, cmakeargs='-P')


@unittest.skipIf(not tools._c_library_avail, "C Library not installed")
def test_CMakeModelDriver_error_notarget():
    r"""Test CMakeModelDriver error for invalid target."""
    makedir, target = os.path.split(scripts['cmake'])
    nt.assert_raises(RuntimeError, CMakeModelDriver, 'test', 'invalid',
                     sourcedir=makedir)


@unittest.skipIf(not tools._c_library_avail, "C Library not installed")
def test_CMakeModelDriver_error_nofile():
    r"""Test CMakeModelDriver error for missing CMakeLists.txt."""
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
        self.builddir = os.path.join(self.sourcedir, 'build')
        self.args = [self.target]
        # self._inst_kwargs['yml']['working_dir']
        self._inst_kwargs['yml']['working_dir'] = self.sourcedir

    def test_sbdir(self):
        r"""Test that source/build directories set correctly."""
        nt.assert_equal(self.instance.sourcedir, self.sourcedir)
        nt.assert_equal(self.instance.builddir, self.builddir)
        

@unittest.skipIf(not tools._c_library_avail, "C Library not installed")
class TestCMakeModelDriverNoStart(TestCMakeModelParam,
                                  parent.TestModelDriverNoStart):
    r"""Test runner for CMakeModelDriver without start."""
    
    def __init__(self, *args, **kwargs):
        super(TestCMakeModelDriverNoStart, self).__init__(*args, **kwargs)
        # Version specifying sourcedir via working_dir
        self._inst_kwargs['yml']['working_dir'] = self.sourcedir
        # Relative paths
        self._inst_kwargs['sourcedir'] = './'
        self._inst_kwargs['builddir'] = 'build'
        self._inst_kwargs['cmakeargs'] = '-Wdev'

    # Done in driver, but driver not started
    def teardown(self):
        r"""Remove the instance, stoppping it."""
        self.instance.cleanup()
        super(TestCMakeModelDriverNoStart, self).teardown()
        

@unittest.skipIf(not tools._c_library_avail, "C Library not installed")
class TestCMakeModelDriver(TestCMakeModelParam, parent.TestModelDriver):
    r"""Test runner for CMakeModelDriver."""
    pass
