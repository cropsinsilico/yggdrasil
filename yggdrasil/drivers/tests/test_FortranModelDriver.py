import os
import yggdrasil.drivers.tests.test_CompiledModelDriver as parent
from yggdrasil.drivers.FortranModelDriver import FortranModelDriver


class TestFortranModelParam(parent.TestCompiledModelParam):
    r"""Test parameters for FortranModelDriver."""

    driver = 'FortranModelDriver'
    
    def __init__(self, *args, **kwargs):
        super(TestFortranModelParam, self).__init__(*args, **kwargs)
        script_dir = os.path.dirname(self.src[0])
        self.args = [self.args[0], '1']
        if FortranModelDriver.is_installed():
            compiler = FortranModelDriver.get_tool('compiler')
            linker = FortranModelDriver.get_tool('linker')
            include_flag = compiler.create_flag('include_dirs', script_dir)
            library_flag = linker.create_flag('library_dirs', script_dir)
            self._inst_kwargs.update(compiler_flags=include_flag,
                                     linker_flags=library_flag)


class TestFortranModelDriverNoInit(TestFortranModelParam,
                                   parent.TestCompiledModelDriverNoInit):
    r"""Test runner for FortranModelDriver without init."""

    def get_test_types(self):
        r"""Return the list of tuples mapping json type to expected native type."""
        out = super(TestFortranModelDriverNoInit, self).get_test_types()
        for i, (k, v) in enumerate(out):
            knew = k
            vnew = v
            if vnew == '*':
                knew = {'type': knew, 'subtype': 'float',
                        'precision': 32}
                vnew = 'real(kind = 4)'
                if k == '1darray':
                    knew['length'] = 3
                    vnew += ', dimension(3)'
                elif k == 'ndarray':
                    knew['shape'] = (3, 4)
                    vnew += ', dimension(3,4)'
            elif 'X' in vnew:
                if vnew.startswith('complex'):
                    knew = {'type': knew, 'precision': 128}
                elif 'ISO_10646' in vnew:
                    knew = {'type': knew, 'precision': 4 * 64}
                else:
                    knew = {'type': knew, 'precision': 64}
                vnew = vnew.replace('X', '8')
            if vnew.startswith('ygg'):
                vnew = 'type(%s)' % vnew
            out[i] = (knew, vnew)
                
        return out
    
    def test_write_function_def(self, *args, **kwargs):
        r"""Test writing and running a function definition."""
        kwargs['declare_functions_as_var'] = True
        super(TestFortranModelDriverNoInit, self).test_write_function_def(*args, **kwargs)
        
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

    def test_write_function_def_return(self):
        r"""Test writing and running a function definition that returns output
        (rather than passing output but parameter reference)."""
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
                                     guess_at_outputs_in_inputs=True)

    def test_write_function_def_guess(self):
        r"""Test writing and running a function definition where outputs
        are determined from the intents."""
        inputs = [{'name': 'x', 'value': 1.0,
                   'datatype': {'type': 'float',
                                'precision': 32,
                                'units': 'cm'}}]
        outputs = [{'name': 'y',
                    'datatype': {'type': 'float',
                                 'precision': 32,
                                 'units': 'cm'}}]
        self.test_write_function_def(inputs=inputs, outputs=outputs,
                                     guess_at_outputs_in_inputs=True)

    def test_write_try_except(self, **kwargs):
        r"""Test writing a try/except block."""
        pass

    def test_split_line(self, vals=None):
        r"""Test split_line."""
        if vals is None:
            vals = [('abcdef', {'length': 3, 'force_split': True},
                     ['ab&', '     &cdef']),
                    ('    abc', {'length': 3, 'force_split': True},
                     ['    abc'])]
        super(TestFortranModelDriverNoInit, self).test_split_line(vals=vals)

            
class TestFortranModelDriverNoStart(TestFortranModelParam,
                                    parent.TestCompiledModelDriverNoStart):
    r"""Test runner for FortranModelDriver without start."""

    def test_parse_arguments(self):
        r"""Run test to initialize driver using the executable."""
        x = os.path.splitext(self.instance.source_files[0])[0] + '.out'
        new_inst = self.import_cls('test_name', [x], skip_compile=True)
        self.assert_equal(new_inst.model_file, x)
        self.assert_equal(new_inst.source_files, self.instance.source_files[:1])
        

class TestFortranModelDriver(TestFortranModelParam,
                             parent.TestCompiledModelDriver):
    r"""Test runner for FortranModelDriver."""
    pass
