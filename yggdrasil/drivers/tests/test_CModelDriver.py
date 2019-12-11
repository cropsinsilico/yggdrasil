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

    def get_test_types(self):
        r"""Return the list of tuples mapping json type to expected native type."""
        out = super(TestCModelDriverNoInit, self).get_test_types()
        for i, (k, v) in enumerate(out):
            if v == '*':
                knew = {'type': k, 'subtype': 'float',
                        'precision': 32}
                vnew = 'float*'
                out[i] = (knew, vnew)
            elif 'X' in v:
                knew = {'type': k, 'precision': 64}
                if k == 'complex':
                    vnew = v.replace('X', 'float')
                else:
                    vnew = v.replace('X', '64')
                out[i] = (knew, vnew)
        return out
    
    def test_write_try_except(self, **kwargs):
        r"""Test writing a try/except block."""
        if self.import_cls.language == 'c':
            self.assert_raises(NotImplementedError, self.import_cls.write_try_except,
                               None, None)
        else:
            super(TestCModelDriverNoInit, self).test_write_try_except(**kwargs)

    def test_write_function_def_single(self):
        r"""Test writing and running a function definition with single output."""
        inputs = [{'name': 'x', 'value': 1.0,
                   'datatype': {'type': 'float',
                                'precision': 32,
                                'units': 'cm'}}]
        outputs = [{'name': 'y',
                    'datatype': {'type': 'float',
                                 'precision': 32,
                                 'units': 'cm'}}]
        self.test_write_function_def(inputs=inputs, outputs=outputs,
                                     outputs_in_inputs=False,
                                     dont_add_lengths=True)
        
    def test_write_function_def_void(self):
        r"""Test writing and running a function definition with no output."""
        inputs = [{'name': 'x', 'value': 1.0,
                   'datatype': {'type': 'float',
                                'precision': 32,
                                'units': 'cm'}}]
        outputs = []
        self.test_write_function_def(inputs=inputs, outputs=outputs,
                                     outputs_in_inputs=False)
        
    def test_write_function_def_string(self):
        r"""Test writing and running a function definition with no length var."""
        inputs = [{'name': 'x', 'value': '"hello"',
                   'length_var': 'length_x',
                   'datatype': {'type': 'string',
                                'precision': 20,
                                'units': ''}},
                  {'name': 'length_x', 'value': 5,
                   'datatype': {'type': 'uint',
                                'precision': 64},
                   'is_length_var': True}]
        outputs = [{'name': 'y',
                    'length_var': 'length_y',
                    'datatype': {'type': 'string',
                                 'precision': 20,
                                 'units': ''}},
                   {'name': 'length_y',
                    'datatype': {'type': 'uint',
                                 'precision': 64},
                    'is_length_var': True}]
        self.test_write_function_def(inputs=inputs, outputs=outputs,
                                     dont_add_lengths=True)
        
    
class TestCModelDriverNoStart(TestCModelParam,
                              parent.TestCompiledModelDriverNoStart):
    r"""Test runner for CModelDriver without start."""

    def test_call_linker(self):
        r"""Test call_linker with static."""
        out = self.instance.compile_model(dont_link=True,
                                          out=None)
        self.instance.call_linker(out, for_model=True,
                                  working_dir=self.instance.working_dir,
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
