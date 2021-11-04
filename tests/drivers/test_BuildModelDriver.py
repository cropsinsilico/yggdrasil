import pytest
from tests.drivers.test_CompiledModelDriver import (
    TestCompiledModelDriver as base_class)
import os
import shutil


class TestBuildModelDriver(base_class):
    r"""Test parameters for BuildModelDriver."""

    parametrize_language = []
    
    test_build = None
    test_call_linker = None
    test_parse_arguments = None
    test_get_tool = None
    test_get_dependency_info = None
    test_get_dependency_source = None
    test_get_dependency_object = None
    test_get_dependency_library = None
    test_get_dependency_include_dirs = None
    test_get_dependency_order = None
    test_invalid_function_param = None
    test_compilers = None
    test_compile_model = None  # TODO: Verify
    test_get_linker_flags = None  # TODO: Verify
    
    @pytest.fixture
    def sourcedir(self, source):
        r"""Directory that source code is in."""
        return os.path.dirname(source[0])

    @pytest.fixture
    def target(self, source):
        r"""Make target that should be used."""
        return os.path.basename(source[0])
    
    @pytest.fixture
    def instance_args(self, name, target):
        r"""Arguments for a new instance of the tested class."""
        return (name, target)

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
