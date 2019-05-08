import os
import re
import unittest
import tempfile
from yggdrasil import platform
from yggdrasil.tests import scripts, assert_raises, assert_equal
import yggdrasil.drivers.tests.test_CompiledModelDriver as parent
from yggdrasil.drivers.CMakeModelDriver import CMakeModelDriver


_driver_installed = CMakeModelDriver.is_installed()


@unittest.skipIf(not _driver_installed, "C Library not installed")
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
    testlist = [(['-DYGG'], [], ['ADD_DEFINITIONS(-DYGG)']),
                (['-Wall'], [], ['ADD_DEFINITIONS(-Wall)']),
                (['/nologo'], [], ['ADD_DEFINITIONS(/nologo)']),
                (['-Iinclude_dir'], [], ['INCLUDE_DIRECTORIES(include_dir)']),
                ([], ['-lm'], ['TARGET_LINK_LIBRARIES(%s -lm)' % target]),
                ([], ['-Llib_dir'], ['LINK_DIRECTORIES(lib_dir)']),
                ([], ['/LIBPATH:"lib_dir"'], ['LINK_DIRECTORIES(lib_dir)']),
                ([], ['m'], ['TARGET_LINK_LIBRARIES(%s m)' % target])]
    if CMakeModelDriver.add_libraries:
        testlist += [([], [fname_dll], ['ADD_LIBRARY(test SHARED IMPORTED)']),
                     ([], [fname_lib], ['ADD_LIBRARY(test STATIC IMPORTED)'])]
    else:
        if platform._is_win:  # pragma: windows
            tempdir_cp = tempdir.replace('\\', re.escape('\\'))
        else:
            tempdir_cp = tempdir
        testlist += [([], [fname_dll], [('FIND_LIBRARY(TEST_LIBRARY NAMES %s '
                                         'test HINTS %s)')
                                        % (os.path.basename(fname_dll), tempdir_cp)]),
                     ([], [fname_lib], [('FIND_LIBRARY(TEST_LIBRARY NAMES %s '
                                         'test HINTS %s)')
                                        % (os.path.basename(fname_lib), tempdir_cp)])]
    from yggdrasil.drivers.CModelDriver import CModelDriver
    CModelDriver.compile_dependencies()
    CMakeModelDriver.compile_dependencies()
    for c, l, lines in testlist:
        out = CMakeModelDriver.create_include(None, target, compile_flags=c,
                                              linker_flags=l)
        for x in lines:
            assert(x in out)
    for fname in [fname_dll, fname_lib]:
        os.remove(fname)
    assert_raises(ValueError, CMakeModelDriver.create_include,
                  None, target, compile_flags=['invalid'])
    assert_raises(ValueError, CMakeModelDriver.create_include,
                  None, target, linker_flags=['-invalid'])
    assert_raises(ValueError, CMakeModelDriver.create_include,
                  None, target, linker_flags=['/invalid'])


@unittest.skipIf(_driver_installed, "C Library installed")
def test_CMakeModelDriver_no_C_library():  # pragma: windows
    r"""Test CMakeModelDriver error when C library not installed."""
    assert_raises(RuntimeError, CMakeModelDriver, 'test', scripts['cmake'])


@unittest.skipIf(not _driver_installed, "C Library not installed")
def test_CMakeModelDriver_error_cmake():
    r"""Test CMakeModelDriver error for invalid cmake args."""
    makedir, target = os.path.split(scripts['cmake'])
    assert_raises(RuntimeError, CMakeModelDriver, 'test', target,
                  sourcedir=makedir, compiler_flags='-P')


@unittest.skipIf(not _driver_installed, "C Library not installed")
def test_CMakeModelDriver_error_notarget():
    r"""Test CMakeModelDriver error for invalid target."""
    makedir, target = os.path.split(scripts['cmake'])
    assert_raises(RuntimeError, CMakeModelDriver, 'test', 'invalid',
                  sourcedir=makedir)


@unittest.skipIf(not _driver_installed, "C Library not installed")
def test_CMakeModelDriver_error_nofile():
    r"""Test CMakeModelDriver error for missing CMakeLists.txt."""
    assert_raises(RuntimeError, CMakeModelDriver, 'test', 'invalid')


class TestCMakeModelParam(parent.TestCompiledModelParam):
    r"""Test parameters for CMakeModelDriver."""

    driver = 'CMakeModelDriver'
    
    def __init__(self, *args, **kwargs):
        super(TestCMakeModelParam, self).__init__(*args, **kwargs)
        self.attr_list += ['target', 'sourcedir', 'builddir']
        self.sourcedir, self.target = os.path.split(scripts['cmake'])
        self.builddir = os.path.join(self.sourcedir, 'build')
        self.args = [self.target]
        # self._inst_kwargs['yml']['working_dir']
        self._inst_kwargs['yml']['working_dir'] = self.sourcedir

    def test_sbdir(self):
        r"""Test that source/build directories set correctly."""
        assert_equal(self.instance.sourcedir, self.sourcedir)
        assert_equal(self.instance.builddir, self.builddir)
        

class TestCMakeModelDriverNoStart(TestCMakeModelParam,
                                  parent.TestCompiledModelDriverNoStart):
    r"""Test runner for CMakeModelDriver without start."""
    
    def __init__(self, *args, **kwargs):
        super(TestCMakeModelDriverNoStart, self).__init__(*args, **kwargs)
        # Version specifying sourcedir via working_dir
        self._inst_kwargs['yml']['working_dir'] = self.sourcedir
        # Relative paths
        self._inst_kwargs.update(sourcedir='.',
                                 builddir='build',
                                 compiler_flags=['-Wdev'])


class TestCMakeModelDriver(TestCMakeModelParam, parent.TestCompiledModelDriver):
    r"""Test runner for CMakeModelDriver."""
    pass
