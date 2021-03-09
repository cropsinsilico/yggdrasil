import os
import shutil
import yggdrasil.drivers.tests.test_CompiledModelDriver as parent


class TestBuildModelParam(parent.TestCompiledModelParam):
    r"""Test parameters for BuildModelDriver."""
    pass


class TestBuildModelDriverNoInit(TestBuildModelParam,
                                 parent.TestCompiledModelDriverNoInit):
    """Test runner for BuildModelDriver without creating an instance."""

    test_build = None
    test_get_tool = None
    test_get_dependency_info = None
    test_get_dependency_source = None
    test_get_dependency_object = None
    test_get_dependency_library = None
    test_get_dependency_include_dirs = None
    test_get_dependency_order = None
    test_invalid_function_param = None


class TestBuildModelDriverNoStart(TestBuildModelParam,
                                  parent.TestCompiledModelDriverNoStart):
    r"""Test runner for BuildModelDriver without start."""

    test_compilers = None

    def test_get_language_for_source(self):
        r"""Test the get_language_for_source method."""
        buildfile = None
        if self.import_cls.buildfile_base:
            buildfile = os.path.join(os.path.dirname(self.src[0]),
                                     self.import_cls.buildfile_base)
            buildfile_cache = '_copy'.join(os.path.splitext(buildfile))
        self.import_cls.get_language_for_source(self.src)
        self.import_cls.get_language_for_source(os.path.dirname(self.src[0]))
        try:
            if buildfile:
                shutil.move(buildfile, buildfile_cache)
            self.import_cls.get_language_for_source(self.src[0])
        finally:
            if buildfile:
                shutil.move(buildfile_cache, buildfile)


class TestBuildModelDriver(TestBuildModelParam,
                           parent.TestCompiledModelDriver):
    r"""Test runner for BuildModelDriver."""
    pass
