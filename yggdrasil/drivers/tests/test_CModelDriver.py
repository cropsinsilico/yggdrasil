import os
import unittest
from yggdrasil import platform
import yggdrasil.drivers.tests.test_CompiledModelDriver as parent
from yggdrasil.drivers.CModelDriver import _incl_interface


class TestCModelParam(parent.TestCompiledModelParam):
    r"""Test parameters for CModelDriver."""

    driver = 'CModelDriver'
    
    def __init__(self, *args, **kwargs):
        super(TestCModelParam, self).__init__(*args, **kwargs)
        script_dir = os.path.dirname(self.src[0])
        self.args = [self.args[0], '1']
        self._inst_kwargs.update(compiler_flags=['-I' + script_dir],
                                 linker_flags=['-L' + script_dir])


class TestCModelDriverNoStart(TestCModelParam,
                              parent.TestCompiledModelDriverNoStart):
    r"""Test runner for CModelDriver without start."""

    @unittest.skipIf(not platform._is_linux, "OS is not Linux")
    def test_update_ld_library_path(self):
        r"""Test update_ld_library_path method."""
        total = os.pathsep.join(['test', _incl_interface])
        env = {'LD_LIBRARY_PATH': 'test'}
        env = self.import_cls.update_ld_library_path(env)
        self.assert_equal(env['LD_LIBRARY_PATH'], total)
        # Second time to ensure that path not added twice
        env = self.import_cls.update_ld_library_path(env)
        self.assert_equal(env['LD_LIBRARY_PATH'], total)


class TestCModelDriver(TestCModelParam, parent.TestCompiledModelDriver):
    r"""Test runner for CModelDriver."""
    pass
