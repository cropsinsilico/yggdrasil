import pytest
from tests.drivers.test_CompiledModelDriver import (
    TestCompiledModelDriver as base_class)
import os
import shutil


class TestBuildModelDriver(base_class):
    r"""Test parameters for BuildModelDriver."""

    parametrize_language = []
    
    test_build = None
    test_parse_arguments = None
    test_invalid_function_param = None
    
    @pytest.fixture
    def sourcedir(self, source):
        r"""Directory that source code is in."""
        return os.path.dirname(source[0])

    @pytest.fixture
    def target(self, source):
        r"""Make target that should be used."""
        return os.path.basename(os.path.splitext(source[0])[0])

    @pytest.fixture
    def buildfile(self, sourcedir, python_class):
        r"""Build file path."""
        return os.path.join(sourcedir, python_class.buildfile_base)
    
    @pytest.fixture
    def builddir(self):
        r"""Build file path."""
        return None
    
    @pytest.fixture
    def instance_args(self, name, target):
        r"""Arguments for a new instance of the tested class."""
        return (name, target)

    @pytest.fixture
    def instance_kwargs(self, testing_options, timeout, working_dir,
                        polling_interval, namespace, source,
                        buildfile, builddir):
        r"""Keyword arguments for a new instance of the tested class."""
        return dict(testing_options.get('kwargs', {}),
                    yml={'working_dir': working_dir},
                    timeout=timeout, sleeptime=polling_interval,
                    namespace=namespace, buildfile=buildfile,
                    builddir=builddir, remove_products=True)
    
    def test_get_language_for_source(self, python_class, source):
        r"""Test the get_language_for_source method."""
        buildfile = None
        if python_class.buildfile_base:
            buildfile = os.path.join(os.path.dirname(source[0]),
                                     python_class.buildfile_base)
            buildfile_cache = '_copy'.join(os.path.splitext(buildfile))
        python_class.get_language_for_source(source)
        python_class.get_language_for_source(os.path.dirname(source[0]))
        try:
            if buildfile:
                shutil.move(buildfile, buildfile_cache)
            python_class.get_language_for_source(source[0])
        finally:
            if buildfile:
                shutil.move(buildfile_cache, buildfile)
