import os
import re
import pprint
import tempfile
from yggdrasil import platform
from yggdrasil.tests import (
    scripts, assert_raises, assert_equal, requires_language)
import yggdrasil.drivers.tests.test_CompiledModelDriver as parent
from yggdrasil.drivers.CMakeModelDriver import (
    CMakeModelDriver, CMakeConfigure, CMakeBuilder)


@requires_language('cmake', installed='any')
def test_CMakeConfigure():
    r"""Test CMakeConfigure."""
    src = scripts['c'][0]
    sourcedir = os.path.dirname(src)
    builddir = sourcedir
    # Test get_output_file
    out = CMakeConfigure.get_output_file(src, dont_build=True)
    assert_equal(out, builddir)
    out = CMakeConfigure.get_output_file(src, dont_build=True,
                                         builddir='.', working_dir=sourcedir)
    assert_equal(out, builddir)
    # Test get_flags
    out_A = CMakeConfigure.get_flags(dont_link=True)
    out_B = CMakeConfigure.get_flags(dont_link=True, outfile='.')
    assert_equal(out_A, out_B)


@requires_language('cmake', installed='any')
def test_CMakeBuilder():
    r"""Test CMakeBuilder."""
    src = scripts['c'][0]
    target = os.path.splitext(os.path.basename(src))[0]
    builddir = os.path.dirname(src)
    obj = os.path.splitext(src)[0] + '.obj'
    out = os.path.splitext(src)[0]
    if platform._is_win:  # pragma: windows
        out += '.exe'
    # Test get_output_file
    assert_equal(CMakeBuilder.get_output_file(obj), out)
    assert_equal(CMakeBuilder.get_output_file(obj, target='clean'), 'clean')
    assert_equal(CMakeBuilder.get_output_file(builddir, target=target), out)
    assert_raises(RuntimeError, CMakeBuilder.get_output_file, builddir)
    # Test get_flags
    out_A = CMakeBuilder.get_flags(target=target, working_dir=builddir)
    out_B = CMakeBuilder.get_flags(target=target,
                                   outfile=os.path.join('.', os.path.basename(out)))
    assert_equal(out_A, out_B)


@requires_language('cmake')
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
    if CMakeConfigure.add_libraries:  # pragma: debug
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
        out = CMakeConfigure.create_include(None, target, compile_flags=c,
                                            linker_flags=l, verbose=True)
        for x in lines:
            try:
                assert(x in out)
            except AssertionError:  # pragma: debug
                print("Could not find '%s':" % x)
                pprint.pprint(out)
                raise
    for fname in [fname_dll, fname_lib]:
        os.remove(fname)
    assert_raises(ValueError, CMakeConfigure.create_include,
                  None, target, compile_flags=['invalid'])
    assert_raises(ValueError, CMakeConfigure.create_include,
                  None, target, linker_flags=['-invalid'])
    assert_raises(ValueError, CMakeConfigure.create_include,
                  None, target, linker_flags=['/invalid'])


@requires_language('cmake', installed=False)
def test_CMakeModelDriver_no_C_library():  # pragma: windows
    r"""Test CMakeModelDriver error when C library not installed."""
    assert_raises(RuntimeError, CMakeModelDriver, 'test', scripts['cmake'])


@requires_language('cmake')
def test_CMakeModelDriver_error_cmake():
    r"""Test CMakeModelDriver error for invalid cmake args."""
    makedir, target = os.path.split(scripts['cmake'])
    assert_raises(RuntimeError, CMakeModelDriver, 'test', target,
                  sourcedir=makedir, compiler_flags='-P',
                  target_language='c')


@requires_language('cmake')
def test_CMakeModelDriver_error_notarget():
    r"""Test CMakeModelDriver error for invalid target."""
    makedir, target = os.path.split(scripts['cmake'])
    assert_raises(RuntimeError, CMakeModelDriver, 'test', 'invalid',
                  sourcedir=makedir, target_language='c')


@requires_language('cmake')
def test_CMakeModelDriver_error_nofile():
    r"""Test CMakeModelDriver error for missing CMakeLists.txt."""
    assert_raises(RuntimeError, CMakeModelDriver, 'test', 'invalid',
                  target_language='c')


class TestCMakeModelParam(parent.TestCompiledModelParam):
    r"""Test parameters for CMakeModelDriver."""

    driver = 'CMakeModelDriver'
    
    def __init__(self, *args, **kwargs):
        super(TestCMakeModelParam, self).__init__(*args, **kwargs)
        self.attr_list += ['target', 'sourcedir', 'builddir']
        self.sourcedir, self.target = os.path.split(scripts['cmake'])
        self.builddir = os.path.join(self.sourcedir, 'build')
        self.args = [self.target]
        self._inst_kwargs['yml']['working_dir'] = self.sourcedir

    def test_sbdir(self):
        r"""Test that source/build directories set correctly."""
        assert_equal(self.instance.sourcedir, self.sourcedir)
        assert_equal(self.instance.builddir, self.builddir)
        

class TestCMakeModelDriverNoInit(TestCMakeModelParam,
                                 parent.TestCompiledModelDriverNoInit):
    r"""Test runner for CMakeModelDriver without init."""
    
    def test_sbdir(self):
        r"""Test that source/build directories set correctly."""
        pass
    
    
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

    def test_call_compiler(self):
        r"""Test call_compiler without full path."""
        # self.instance.cleanup()
        self.import_cls.call_compiler(self.instance.source_files,
                                      builddir='build',
                                      working_dir=self.instance.working_dir,
                                      dont_build=True)
        self.import_cls.call_compiler(self.instance.source_files,
                                      out=self.instance.model_file,
                                      builddir='build',
                                      working_dir=self.instance.working_dir,
                                      overwrite=True)
        

class TestCMakeModelDriver(TestCMakeModelParam, parent.TestCompiledModelDriver):
    r"""Test runner for CMakeModelDriver."""

    def test_write_wrappers(self):
        r"""Test write_wrappers method with verbosity and existing
        include file."""
        self.instance.write_wrappers(verbose=True)
