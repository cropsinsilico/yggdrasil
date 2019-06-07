import os
import unittest
from yggdrasil import platform
import yggdrasil.drivers.tests.test_CompiledModelDriver as parent
from yggdrasil.drivers.CModelDriver import CModelDriver


class TestCModelParam(parent.TestCompiledModelParam):
    r"""Test parameters for CModelDriver."""

    driver = 'CModelDriver'
    
    def __init__(self, *args, **kwargs):
        super(TestCModelParam, self).__init__(*args, **kwargs)
        script_dir = os.path.dirname(self.src[0])
        self.args = [self.args[0], '1']
        if CModelDriver.is_installed():
            compiler = CModelDriver.get_tool('compiler')
            linker = CModelDriver.get_tool('linker')
            include_flag = compiler.create_flag('include_dirs', script_dir)
            library_flag = linker.create_flag('library_dirs', script_dir)
            self._inst_kwargs.update(compiler_flags=include_flag,
                                     linker_flags=library_flag)


class TestCModelDriverNoInit(TestCModelParam,
                             parent.TestCompiledModelDriverNoInit):
    r"""Test runner for CModelDriver without init."""

    @unittest.skipIf(not platform._is_linux, "OS is not Linux")
    def test_update_ld_library_path(self):
        r"""Test update_ld_library_path method."""
        lang_dir = self.import_cls.get_language_dir()
        total = os.pathsep.join(['test', lang_dir])
        env = {'LD_LIBRARY_PATH': 'test'}
        env = self.import_cls.update_ld_library_path(env)
        self.assert_equal(env['LD_LIBRARY_PATH'], total)
        # Second time to ensure that path not added twice
        env = self.import_cls.update_ld_library_path(env)
        self.assert_equal(env['LD_LIBRARY_PATH'], total)

    def test_write_try_except(self, **kwargs):
        r"""Test writing a try/except block."""
        if self.import_cls.language == 'c':
            self.assert_raises(NotImplementedError, self.import_cls.write_try_except,
                               None, None)
        else:
            super(TestCModelDriverNoInit, self).test_write_try_except(**kwargs)
        
    
class TestCModelDriverNoStart(TestCModelParam,
                              parent.TestCompiledModelDriverNoStart):
    r"""Test runner for CModelDriver without start."""

    def test_call_linker(self):
        r"""Test call_linker with static."""
        out = self.instance.compile_model(dont_link=True,
                                          out=None)
        self.instance.call_linker(out, for_model=True,
                                  working_dir=self.instance.working_dir,
                                  linker_language='c++',
                                  libtype='static')

    def test_parse_arguments(self):
        r"""Run test to initialize driver using the executable."""
        x = os.path.splitext(self.instance.source_files[0])[0] + '.out'
        new_inst = self.import_cls('test_name', [x], skip_compile=True)
        self.assert_equal(new_inst.model_file, x)
        self.assert_equal(new_inst.source_files, self.instance.source_files[:1])
        

class TestCModelDriver(TestCModelParam, parent.TestCompiledModelDriver):
    r"""Test runner for CModelDriver."""
    pass
