import pytest
from tests.drivers.test_BuildModelDriver import (
    TestBuildModelDriver as base_class)
import os
from yggdrasil import platform
from yggdrasil.drivers.BuildModelDriver import BuildError
from yggdrasil.drivers.CMakeModelDriver import (
    CMakeModelDriver, CMakeConfigure, CMakeBuilder)
from yggdrasil.drivers.CModelDriver import GCCCompiler


@pytest.mark.related_language('cmake')
def test_CMakeConfigure(scripts):
    r"""Test CMakeConfigure."""
    out_A = CMakeConfigure.get_flags(dont_link=True)
    out_B = CMakeConfigure.get_flags(dont_link=True, outfile='.')
    assert out_A == out_B


@pytest.mark.related_language('cmake')
def test_CMakeBuilder(scripts):
    r"""Test CMakeBuilder."""
    src = scripts['c'][0]
    target = os.path.splitext(os.path.basename(src))[0]
    builddir = os.path.dirname(src)
    out = os.path.splitext(src)[0]
    if platform._is_win:  # pragma: windows
        out += '.exe'
    # Test get_flags
    out_A = CMakeBuilder.get_flags(target=target, working_dir=builddir)
    out_B = CMakeBuilder.get_flags(target=target,
                                   outfile=os.path.join('.', os.path.basename(out)))
    assert out_A == out_B


@pytest.mark.absent_language('cmake')
def test_CMakeModelDriver_no_cmake(scripts):  # pragma: windows
    r"""Test CMakeModelDriver error when cmake not installed."""
    with pytest.raises(RuntimeError):
        CMakeModelDriver('test', scripts['cmake'])


@pytest.mark.language('cmake')
@pytest.mark.absent_language('c++')
def test_CMakeModelDriver_no_C_library(scripts):  # pragma: windows
    r"""Test CMakeModelDriver error when C++ library not installed."""
    with pytest.raises(RuntimeError):
        CMakeModelDriver('test', scripts['cmake'])


@pytest.mark.language('cmake')
@pytest.mark.language('c++')
def test_CMakeModelDriver_error_cmake(scripts):
    r"""Test CMakeModelDriver error for invalid cmake args."""
    makedir, target = os.path.split(scripts['cmake'])
    builddir = os.path.join(makedir, 'build')
    assert not os.path.isfile(builddir)
    with pytest.raises(RuntimeError):
        CMakeModelDriver('test', target, working_dir=makedir,
                         sourcedir=makedir, configurer_flags='-P',
                         target_language='c',
                         overwrite=True, remove_products=True)
    assert not os.path.isfile(builddir)


@pytest.mark.language('cmake')
@pytest.mark.language('c++')
def test_CMakeModelDriver_error_notarget(scripts):
    r"""Test CMakeModelDriver error for invalid target."""
    makedir, target = os.path.split(scripts['cmake'])
    builddir = os.path.join(makedir, 'build')
    assert not os.path.isfile(builddir)
    with pytest.raises(RuntimeError):
        CMakeModelDriver('test', 'invalid', working_dir=makedir,
                         sourcedir=makedir, target_language='c',
                         overwrite=True, remove_products=True)
    assert not os.path.isfile(builddir)


@pytest.mark.language('cmake')
@pytest.mark.language('c++')
def test_CMakeModelDriver_error_nofile():
    r"""Test CMakeModelDriver error for missing CMakeLists.txt."""
    sourcedir = os.path.dirname(__file__)
    working_dir = sourcedir
    builddir = os.path.join(sourcedir, 'invalid_build')
    buildfile = os.path.join(sourcedir, 'CMakeLists.txt')
    assert not os.path.isdir(builddir)
    assert not os.path.isfile(buildfile)
    with pytest.raises(BuildError):
        CMakeModelDriver('test', 'invalid', target_language='c',
                         buildfile=buildfile,
                         sourcedir=sourcedir,
                         builddir=os.path.basename(builddir),
                         working_dir=working_dir,
                         overwrite=True, remove_products=True)
    assert not os.path.isdir(builddir)
    assert not os.path.isfile(buildfile)
                         

@pytest.mark.language('c')
@pytest.mark.language('c++')
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

    @pytest.mark.skipif(not platform._is_win, reason="Windows only.")
    @pytest.mark.skipif(not GCCCompiler.is_installed(),
                        reason="GNU compiler not installed.")
    def test_run_model_gcc(self, run_model_instance):
        r"""Test compiling/running test model with gcc."""
        run_model_instance(target_compiler='gcc',
                           remove_products=True)

    def test_sbdir(self, instance, sourcedir, builddir):
        r"""Test that source/build directories set correctly."""
        assert instance.sourcedir == sourcedir
        assert instance.builddir == builddir


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
                    compiler_flags=['-Wdev'], skip_compiler=True,
                    remove_products=True)
