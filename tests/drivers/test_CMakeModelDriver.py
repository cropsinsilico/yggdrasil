import pytest
from tests.drivers.test_BuildModelDriver import (
    TestBuildModelDriver as base_class)
import os
import re
import pprint
import tempfile
from yggdrasil import platform
from yggdrasil.drivers.CMakeModelDriver import (
    CMakeModelDriver, CMakeConfigure, CMakeBuilder)
from yggdrasil.drivers.CModelDriver import GCCCompiler
from yggdrasil.drivers.CPPModelDriver import CPPModelDriver


@pytest.mark.related_language('cmake')
def test_CMakeConfigure(scripts):
    r"""Test CMakeConfigure."""
    src = scripts['c'][0]
    sourcedir = os.path.dirname(src)
    builddir = sourcedir
    # Test get_output_file
    out = CMakeConfigure.get_output_file(src, dont_build=True)
    assert(out == builddir)
    out = CMakeConfigure.get_output_file(src, dont_build=True,
                                         builddir='.', working_dir=sourcedir)
    assert(out == builddir)
    # Test get_flags
    out_A = CMakeConfigure.get_flags(dont_link=True)
    out_B = CMakeConfigure.get_flags(dont_link=True, outfile='.')
    assert(out_A == out_B)


@pytest.mark.related_language('cmake')
def test_CMakeBuilder(scripts):
    r"""Test CMakeBuilder."""
    src = scripts['c'][0]
    target = os.path.splitext(os.path.basename(src))[0]
    builddir = os.path.dirname(src)
    obj = os.path.splitext(src)[0] + '.obj'
    out = os.path.splitext(src)[0]
    if platform._is_win:  # pragma: windows
        out += '.exe'
    # Test get_output_file
    assert(CMakeBuilder.get_output_file(obj) == out)
    assert(CMakeBuilder.get_output_file(obj, target='clean') == 'clean')
    assert(CMakeBuilder.get_output_file(builddir, target=target) == out)
    with pytest.raises(RuntimeError):
        CMakeBuilder.get_output_file(builddir)
    # Test get_flags
    out_A = CMakeBuilder.get_flags(target=target, working_dir=builddir)
    out_B = CMakeBuilder.get_flags(target=target,
                                   outfile=os.path.join('.', os.path.basename(out)))
    assert(out_A == out_B)


@pytest.mark.language('cmake')
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
        tempdir_cp = tempdir
        if platform._is_win:  # pragma: windows
            tempdir_cp = tempdir.replace('\\', re.escape('\\'))
        testlist += [([], [fname_dll], [('FIND_LIBRARY(TEST_LIBRARY NAMES %s '
                                         'test HINTS %s)')
                                        % (os.path.basename(fname_dll), tempdir_cp)]),
                     ([], [fname_lib], [('FIND_LIBRARY(TEST_LIBRARY NAMES %s '
                                         'test HINTS %s)')
                                        % (os.path.basename(fname_lib), tempdir_cp)])]
    from yggdrasil.drivers.CModelDriver import CModelDriver
    CModelDriver.compile_dependencies()
    CMakeModelDriver.compile_dependencies()
    kws = {'compiler': CModelDriver.get_tool('compiler'),
           'linker': CModelDriver.get_tool('linker')}
    for c, l, lines in testlist:
        out = CMakeConfigure.create_include(None, target, compiler_flags=c,
                                            linker_flags=l, verbose=True,
                                            **kws)
        for x in lines:
            try:
                assert(x in out)
            except AssertionError:  # pragma: debug
                print("Could not find '%s':" % x)
                pprint.pprint(out)
                raise
    for fname in [fname_dll, fname_lib]:
        os.remove(fname)
    with pytest.raises(ValueError):
        CMakeConfigure.create_include(
            None, target, compiler_flags=['invalid'], **kws)
    with pytest.raises(ValueError):
        CMakeConfigure.create_include(
            None, target, linker_flags=['-invalid'], **kws)
    with pytest.raises(ValueError):
        CMakeConfigure.create_include(
            None, target, linker_flags=['/invalid'], **kws)


@pytest.mark.absent_language('cmake')
def test_CMakeModelDriver_no_C_library(scripts):  # pragma: windows
    r"""Test CMakeModelDriver error when C library not installed."""
    with pytest.raises(RuntimeError):
        CMakeModelDriver('test', scripts['cmake'])


@pytest.mark.language('cmake')
def test_CMakeModelDriver_error_cmake(scripts):
    r"""Test CMakeModelDriver error for invalid cmake args."""
    makedir, target = os.path.split(scripts['cmake'])
    with pytest.raises(RuntimeError):
        CMakeModelDriver('test', target,
                         sourcedir=makedir, compiler_flags='-P',
                         target_language='c')


@pytest.mark.language('cmake')
def test_CMakeModelDriver_error_notarget(scripts):
    r"""Test CMakeModelDriver error for invalid target."""
    makedir, target = os.path.split(scripts['cmake'])
    with pytest.raises(RuntimeError):
        CMakeModelDriver('test', 'invalid',
                         sourcedir=makedir, target_language='c')


@pytest.mark.language('cmake')
def test_CMakeModelDriver_error_nofile():
    r"""Test CMakeModelDriver error for missing CMakeLists.txt."""
    with pytest.raises(RuntimeError):
        CMakeModelDriver('test', 'invalid',
                         target_language='c')


class TestCMakeModelDriver(base_class):
    r"""Test runner for CMakeModelDriver."""

    @pytest.fixture(scope="class")
    def language(self):
        r"""str: Language being tested."""
        return 'cmake'

    @pytest.fixture
    def builddir(self, sourcedir):
        r"""Directory that build will occur in."""
        return os.path.join(sourcedir, 'build')

    @pytest.fixture(autouse=True)
    def dont_verify_fds(self, verify_count_fds, disable_verify_count_fds):
        r"""Turn off verification, fds linger on windows."""
        yield
    
    @pytest.fixture
    def instance_kwargs(self, testing_options, timeout, sourcedir,
                        polling_interval, namespace, source):
        r"""Keyword arguments for a new instance of the tested class."""
        return dict(testing_options.get('kwargs', {}),
                    yml={'working_dir': sourcedir},
                    timeout=timeout, sleeptime=polling_interval,
                    namespace=namespace, env_compiler='CXX',
                    env_compiler_flags='CXXFLAGS')

    @pytest.mark.skipif(not platform._is_win, reason="Windows only.")
    @pytest.mark.skipif(not GCCCompiler.is_installed(),
                        reason="GNU compiler not installed.")
    def test_run_model_gcc(self, run_model_instance):
        r"""Test compiling/running test model with gcc."""
        run_model_instance(target_compiler='gcc')

    def test_sbdir(self, instance, sourcedir, builddir):
        r"""Test that source/build directories set correctly."""
        assert(instance.sourcedir == sourcedir)
        assert(instance.builddir == builddir)

    def test_write_wrappers(self, instance):
        r"""Test write_wrappers method with verbosity and existing
        include file."""
        try:
            instance.overwrite = False
            instance.write_wrappers(verbose=False)
            instance.write_wrappers(verbose=True)
            instance.overwrite = True
            instance.write_wrappers(verbose=True)
        finally:
            instance.overwrite = True


class TestCMakeModelDriver_wd(TestCMakeModelDriver):
    r"""Test runner for CMakeModelDriver with working directory."""
    
    @pytest.fixture
    def instance_kwargs(self, testing_options, timeout, sourcedir,
                        polling_interval, namespace, source):
        r"""Keyword arguments for a new instance of the tested class."""
        return dict(testing_options.get('kwargs', {}),
                    yml={'working_dir': sourcedir},
                    timeout=timeout, sleeptime=polling_interval,
                    namespace=namespace, env_compiler='CXX',
                    env_compiler_flags='CXXFLAGS',
                    sourcedir='.', builddir='build',
                    compiler_flags=['-Wdev'], skip_compiler=True)
    
    # Disable instance args?

    def test_call_compiler(self, python_class, instance):
        r"""Test call_compiler without full path."""
        # instance.cleanup()
        CPPModelDriver.compile_dependencies()
        python_class.call_compiler(instance.source_files,
                                   builddir='build',
                                   working_dir=instance.working_dir,
                                   dont_build=True)
        out = instance.model_file
        if platform._is_win:
            out = os.path.join(os.path.dirname(out),
                               'Debug',
                               os.path.basename(out))
        compiler = CPPModelDriver.get_tool('compiler')
        python_class.call_compiler(instance.source_files,
                                   out=out,
                                   builddir='build',
                                   working_dir=instance.working_dir,
                                   overwrite=True,
                                   target_compiler=compiler.toolname,
                                   target_linker=compiler.linker().toolname)
