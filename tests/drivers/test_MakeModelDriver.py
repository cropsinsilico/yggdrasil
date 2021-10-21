import pytest
from tests.drivers.test_BuildModelDriver import (
    TestBuildModelDriver as base_class)
import os
from yggdrasil.drivers.MakeModelDriver import MakeModelDriver, MakeCompiler


@pytest.mark.related_language('make')
def test_MakeCompiler():
    r"""Test MakeCompiler class."""
    assert(MakeCompiler.get_output_file(None, target='clean') == 'clean')


@pytest.mark.absent_language('make')
def test_MakeModelDriver_no_C_library(scripts):  # pragma: windows
    r"""Test MakeModelDriver error when C library not installed."""
    with pytest.raises(RuntimeError):
        MakeModelDriver('test', scripts['make'])


@pytest.mark.language('make')
def test_MakeModelDriver_error_notarget(scripts):
    r"""Test MakeModelDriver error for invalid target."""
    makedir, target = os.path.split(scripts['make'])
    with pytest.raises(RuntimeError):
        MakeModelDriver('test', 'invalid', makedir=makedir)


@pytest.mark.language('make')
def test_MakeModelDriver_error_nofile(scripts):
    r"""Test MakeModelDriver error for missing Makefile."""
    makedir, target = os.path.split(scripts['make'])
    with pytest.raises(RuntimeError):
        MakeModelDriver('test', 'invalid')


class TestMakeModelDriver(base_class):
    r"""Test runner for MakeModelDriver."""

    @pytest.fixture(scope="class")
    def language(self):
        r"""str: Language being tested."""
        return 'make'

    @pytest.fixture
    def makefile(self, sourcedir):
        r"""Makefile."""
        return os.path.join(sourcedir, 'Makefile')

    @pytest.fixture
    def instance_kwargs(self, testing_options, timeout, working_dir,
                        polling_interval, namespace, source, makefile):
        r"""Keyword arguments for a new instance of the tested class."""
        return dict(testing_options.get('kwargs', {}),
                    yml={'working_dir': working_dir},
                    timeout=timeout, sleeptime=polling_interval,
                    namespace=namespace, makefile=makefile)


class TestMakeModelDriver_wd(TestMakeModelDriver):
    r"""Test runner for MakeModelDriver with working directory."""

    @pytest.fixture
    def instance_kwargs(self, testing_options, timeout, sourcedir,
                        polling_interval, namespace, source):
        r"""Keyword arguments for a new instance of the tested class."""
        return dict(testing_options.get('kwargs', {}),
                    yml={'working_dir': sourcedir},
                    timeout=timeout, sleeptime=polling_interval,
                    namespace=namespace)

    def test_compile_model(self, target, instance):
        r"""Test compile model with alternate set of input arguments."""
        src = [target + '.c']
        instance.compile_model(target=target)
        instance.compile_model(source_files=src)
        with pytest.raises(RuntimeError):
            instance.compile_model(source_files=src,
                                   target=target + 'invalid')
        

class TestMakeModelDriver_wd_rel(TestMakeModelDriver):
    r"""Test runner for MakeModelDriver with makedir rel to working_dir."""

    @pytest.fixture
    def instance_kwargs(self, testing_options, timeout, working_dir,
                        polling_interval, namespace, source, sourcedir):
        r"""Keyword arguments for a new instance of the tested class."""
        makedir_parts = os.path.split(sourcedir)
        return dict(testing_options.get('kwargs', {}),
                    yml={'working_dir': working_dir},
                    timeout=timeout, sleeptime=polling_interval,
                    namespace=namespace, working_dir=makedir_parts[0],
                    makedir=makedir_parts[1])
