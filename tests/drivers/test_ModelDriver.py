import pytest
from tests.drivers.test_Driver import TestDriver as base_class
import os
import copy
import pprint
import shutil
import logging
from yggdrasil import platform, constants
from yggdrasil.drivers.ModelDriver import ModelDriver, remove_product
from yggdrasil.drivers.CompiledModelDriver import CompiledModelDriver
from yggdrasil.drivers.InterpretedModelDriver import InterpretedModelDriver


def test_remove_product():
    r"""Test remove_product."""
    test_file = os.path.join(os.path.dirname(__file__), 'remove_product_test.py')
    with open(test_file, 'w') as fd:
        fd.write('print(\'hello\')')
    try:
        with pytest.raises(RuntimeError):
            remove_product(test_file, check_for_source=True)
        with pytest.raises(RuntimeError):
            remove_product(os.path.dirname(test_file), check_for_source=True)
    finally:
        os.remove(test_file)


def test_ModelDriver_implementation():
    r"""Test that NotImplementedError raised for base class."""
    with pytest.raises(NotImplementedError):
        ModelDriver.language_executable()
    with pytest.raises(NotImplementedError):
        ModelDriver.executable_command(None)
    with pytest.raises(NotImplementedError):
        ModelDriver.is_library_installed(None)
    with pytest.raises(NotImplementedError):
        CompiledModelDriver.get_tool('compiler')
    with pytest.raises(NotImplementedError):
        InterpretedModelDriver.get_interpreter()


_models = sorted([x for x in (constants.LANGUAGES['interpreted']
                              + constants.LANGUAGES['dsl'])
                  if x not in ['matlab']] + ['executable'])


@pytest.mark.suite("models")
class TestModelDriver(base_class):
    r"""Test parameters for basic ModelDriver class."""

    _component_type = 'model'
    parametrize_language = _models

    @pytest.fixture(scope="class", autouse=True)
    def component_subtype(self, language):
        r"""Subtype of component being tested."""
        return language

    @pytest.fixture(scope="class")
    def language(self, request):
        r"""str: Language being tested."""
        return request.param

    @pytest.fixture(scope="class")
    def required_languages(self, language):
        r"""list: Languages required by the test."""
        return [language]

    @pytest.fixture(scope="class", autouse=True)
    def check_enabled(self, required_languages, check_required_languages):
        r"""Check if the language is enabled/disabled."""
        check_required_languages(required_languages)

    @pytest.fixture(scope="class")
    def source(self, python_class, scripts):
        r"""str: Source code to use for tests."""
        # if python_class.language is not None:
        out = scripts[python_class.language.lower()]
        if not isinstance(out, list):
            out = [out]
        return out

    @pytest.fixture(scope="class")
    def working_dir(self, source):
        r"""Working director."""
        return os.path.dirname(source[0])
    
    @pytest.fixture
    def instance_args(self, name, source, testing_options):
        r"""Arguments for a new instance of the tested class."""
        return tuple(
            [name, source + copy.deepcopy(
                testing_options.get('args', []))])

    @pytest.fixture(scope="class")
    def python_class_installed(self, python_class):
        r"""bool: True if the python class is installed."""
        return python_class.is_installed()

    @pytest.fixture
    def run_model_instance_kwargs(self):
        r"""dict: Additional keyword arguments that should be used in calls
        to run_model_instance"""
        return {}
    
    @pytest.fixture
    def run_model_instance(self, python_class, is_installed,
                           instance_args, instance_kwargs,
                           testing_options, run_model_instance_kwargs):
        r"""Create a driver for a model and run it."""
        if testing_options.get('requires_partner', False):
            pytest.skip(f"{python_class.language} requires partner model "
                        f"to run.")

        def run_model_instance_w(**kwargs):
            inst_kwargs = copy.deepcopy(instance_kwargs)
            inst_kwargs.update(kwargs)
            inst_kwargs.update(run_model_instance_kwargs)
            logger = logging.getLogger("yggdrasil")
            if logger.getEffectiveLevel() >= 20:
                inst_kwargs.setdefault('logging_level', 'INFO')
            drv = python_class(*instance_args, **inst_kwargs)
            getattr(drv, 'numeric_logging_level')
            drv.start()
            drv.wait(False)
            assert(not drv.errors)
            drv.cleanup()
        return run_model_instance_w

    @pytest.fixture(scope="class")
    def run_generated_code(self, python_class, is_installed):
        r"""Write and run generated code."""
        # def run_generated_code_w(lines, **kwargs):
        #     python_class.run_code(lines, **kwargs)
        return python_class.run_code

    @pytest.fixture(scope="class")
    def code_types(self, python_class, testing_options):
        if python_class.type_map is None:
            out = []
        else:
            out = copy.deepcopy(list(python_class.type_map.items()))
            if 'flag' not in python_class.type_map:
                out.append(('flag', python_class.type_map['boolean']))
        out += testing_options.get('code_types', [])
        for k, v in testing_options.get('replacement_code_types', {}).items():
            if k in out:
                out[out.index(k)] = v
        return out
            
    def test_executable_command(self, python_class):
        r"""Test error raise for invalid exec_type."""
        if python_class.executable_type != 'interpreter':
            pytest.skip("Only valid for languages with an interpreter")
        with pytest.raises(ValueError):
            python_class.executable_command([], exec_type='invalid')

    def test_is_installed(self, python_class, is_installed):
        r"""Assert that the tested model driver is installed."""
        assert(python_class.is_installed())

    def test_comm_installed(self, python_class):
        r"""Tests for getting installed comm while skipping config."""
        assert(python_class.is_comm_installed()
               == python_class.is_comm_installed(skip_config=True))
        assert(python_class.is_comm_installed(commtype='invalid',
                                              skip_config=True) is False)
        
    def test_language_version(self, python_class, is_installed):
        r"""Test language version."""
        assert(python_class.language_version())

    def test_python2language(self, python_class, testing_options,
                             nested_approx, pandas_equality_patch):
        r"""Test python2language."""
        for a, b in testing_options.get('python2language', []):
            assert(python_class.python2language(a) == nested_approx(b))
        
    def test_is_library_installed(self, python_class, testing_options):
        r"""Test is_library_installed for invalid library."""
        for x in testing_options.get('valid_libraries', []):
            assert(python_class.is_library_installed(x) is True)
        for x in testing_options.get('invalid_libraries', []):
            assert(python_class.is_library_installed(x) is False)
        
    def test_run_model(self, run_model_instance, testing_options):
        r"""Test running script used without debug."""
        if testing_options.get('requires_partner', False):
            pytest.skip("requires partner model to run")
        run_model_instance()

    @pytest.mark.skipif(platform._is_mac, reason="Valgrind slow on Mac")
    @pytest.mark.skipif(platform._is_win, reason="No valgrind on windows")
    @pytest.mark.skipif(shutil.which('valgrind') is None,
                        reason="Valgrind not installed.")
    def test_valgrind(self, working_dir, uuid, run_model_instance,
                      testing_options):
        r"""Test running with valgrind."""
        if testing_options.get('requires_partner', False):
            pytest.skip("requires partner model to run")
        valgrind_log = f"valgrind_log_{uuid.replace('-', '_')}.log"
        if working_dir:
            valgrind_log = os.path.join(working_dir, valgrind_log)
        try:
            run_model_instance(with_valgrind=True, with_strace=False,
                               valgrind_flags=['--leak-check=full',
                                               f'--log-file={valgrind_log}'])
        finally:
            if os.path.isfile(valgrind_log):
                os.remove(valgrind_log)
    
    @pytest.mark.skipif(platform._is_win or platform._is_mac,
                        reason="No strace on Windows or MacOS")
    @pytest.mark.skipif(shutil.which('strace') is None,
                        reason="strace not installed.")
    def test_strace(self, run_model_instance, testing_options):
        r"""Test running with strace."""
        if testing_options.get('requires_partner', False):
            pytest.skip("requires partner model to run")
        run_model_instance(with_valgrind=False, with_strace=True)
        
    # Tests for code generation
    def test_invalid_function_param(self, python_class, instance_kwargs,
                                    is_installed):
        r"""Test errors raise during class creation when parameters are invalid."""
        kwargs = copy.deepcopy(instance_kwargs)
        kwargs['name'] = 'test'
        kwargs['args'] = ['test']
        kwargs['function'] = 'invalid'
        kwargs['source_files'] = []
        if python_class.function_param is None:
            with pytest.raises(ValueError):
                python_class(**kwargs)
        else:
            kwargs['args'] = ['invalid']
            with pytest.raises(ValueError):
                python_class(**kwargs)
            kwargs['source_files'] = ['invalid']
            with pytest.raises(ValueError):
                python_class(**kwargs)
                               
    def test_get_native_type(self, python_class, code_types):
        r"""Test translation to native type."""
        for a, b in code_types:
            assert(python_class.get_native_type(datatype=a) == b)
            if not isinstance(a, dict):
                assert(
                    python_class.get_native_type(datatype={'type': a}) == b)
                if a in ['float', 'int', 'uint']:
                    assert(python_class.get_native_type(
                        datatype={'type': 'scalar', 'subtype': a}) == b)
                
    def test_write_declaration(self, python_class, code_types):
        r"""Test write_declaration for all supported native types."""
        if (((python_class.function_param is None)
             or ('declare' not in python_class.function_param))):
            pytest.skip("No declaration token")
        for a, b in code_types:
            python_class.write_declaration({'name': 'test', 'datatype': a})

    def test_write_model_wrapper(self, python_class):
        r"""Test writing a model based on yaml parameters."""
        if python_class.function_param is None:
            with pytest.raises(NotImplementedError):
                python_class.write_model_wrapper(None, None)
            with pytest.raises(NotImplementedError):
                python_class.write_model_recv(None, None)
            with pytest.raises(NotImplementedError):
                python_class.write_model_send(None, None)
        else:
            inputs = [
                {'name': 'a', 'datatype': 'bytes', 'outside_loop': True},
                {'name': 'b', 'datatype': {'type': 'int', 'precision': 64}},
                {'name': 'c', 'datatype': {'type': 'string', 'precision': 10}}]
            outputs = [
                {'name': 'y', 'datatype': {'type': 'float', 'precision': 32}},
                {'name': 'z', 'datatype': 'bytes', 'outside_loop': True},
                {'name': 'x', 'datatype': {'type': 'string', 'precision': 10}}]
            for iovar in [inputs, outputs]:
                for x in iovar:
                    x['name'] = 'test:' + x['name']
            python_class.write_model_wrapper('test', 'test',
                                             inputs=inputs,
                                             outputs=outputs)
            with pytest.raises(NotImplementedError):
                python_class.format_function_param('invalid_key')
        
    def test_write_executable(self, python_class):
        r"""Test writing an executable."""
        if python_class.function_param is None:
            with pytest.raises(NotImplementedError):
                python_class.write_executable(None)
        else:
            lines1 = python_class.write_executable('dummy',
                                                   prefix='dummy',
                                                   suffix='dummy')
            lines2 = python_class.write_executable(lines1)
            assert(lines1 == lines2)
            # Don't run this because it is invalid

    def test_error_code(self, python_class, is_installed):
        r"""Test that error is raised when code generates one."""
        if python_class.function_param is None:
            pytest.skip("Language not tokenized")
            return
        error_msg = 'Test error'
        lines = [python_class.function_param['error'].format(error_msg=error_msg)]
        with pytest.raises(RuntimeError):
            python_class.run_code(lines)

    @pytest.fixture(scope="class")
    def write_function_def(self, python_class, run_generated_code):
        r"""Write & run a function definition."""
        def write_function_def_w(inputs=None, outputs=None,
                                 outputs_in_inputs=None,
                                 declare_functions_as_var=None,
                                 guess_at_outputs_in_inputs=False, **kwargs):
            if declare_functions_as_var is None:
                declare_functions_as_var = False
            assert(inputs is not None)
            assert(outputs is not None)
            if outputs_in_inputs is None:
                outputs_in_inputs = python_class.outputs_in_inputs
            flag_var = {'name': 'flag',
                        'datatype': 'flag',
                        'value': python_class.function_param['true']}
            function_contents = []
            if len(inputs) == len(outputs):
                for i, o in zip(inputs, outputs):
                    function_contents += python_class.write_assign_to_output(
                        o['name'], i['name'],
                        outputs_in_inputs=outputs_in_inputs)
                    function_contents += python_class.write_print_output_var(
                        o['name'], in_inputs=outputs_in_inputs)
            output_var = python_class.prepare_output_variables(
                outputs, in_inputs=python_class.outputs_in_inputs,
                in_definition=True)
            if not python_class.types_in_funcdef:
                kwargs['outputs'] = outputs
            definition = python_class.write_function_def(
                'test_function', inputs=inputs, output_var=output_var,
                function_contents=function_contents,
                flag_var=flag_var, outputs_in_inputs=outputs_in_inputs,
                print_inputs=True, print_outputs=True, **kwargs)
            # Add second definition to test ability to locate specific
            # function in the presence of others
            definition.append('')
            definition += python_class.write_function_def(
                'test_function_decoy', inputs=inputs,
                outputs=outputs, flag_var=flag_var,
                function_contents=function_contents,
                outputs_in_inputs=outputs_in_inputs,
                skip_interface=True)
            parsed = None
            try:
                kwargs = dict(contents='\n'.join(definition),
                              expected_outputs=outputs,
                              outputs_in_inputs=outputs_in_inputs)
                if guess_at_outputs_in_inputs:
                    kwargs.pop('expected_outputs')
                    kwargs.pop('outputs_in_inputs')
                parsed = python_class.parse_function_definition(
                    None, 'test_function', **kwargs)
                assert(len(parsed.get('inputs', [])) == len(inputs))
                assert(len(parsed.get('outputs', [])) == len(outputs))
            except BaseException:  # pragma: debug
                pprint.pprint(definition)
                if parsed:
                    pprint.pprint(parsed)
                    print("Expected inputs:")
                    pprint.pprint(inputs)
                    print("Expected outputs:")
                    pprint.pprint(outputs)
                raise
            if inputs:
                for xp, x0 in zip(parsed['inputs'], inputs):
                    assert(xp['name'] == x0['name'])
                    x0.update(xp)
            if outputs:
                for xp, x0 in zip(parsed['outputs'], outputs):
                    assert(xp['name'] == x0['name'])
                    x0.update(xp)
            # Lines required to set up the function call
            lines = []
            if 'declare' in python_class.function_param:
                for x in inputs + outputs:
                    lines += python_class.write_declaration(x)
                if outputs_in_inputs:
                    lines += python_class.write_declaration(flag_var)
                if declare_functions_as_var:
                    if outputs_in_inputs:
                        lines += python_class.write_declaration(
                            dict(flag_var, name='test_function'))
                    elif len(outputs) > 0:
                        lines += python_class.write_declaration(
                            dict(outputs[0], name='test_function'))
            for x in inputs:
                lines.append(python_class.format_function_param(
                    'assign', **x))
            if outputs_in_inputs:
                lines.append(python_class.format_function_param(
                    'assign', **flag_var))
            lines += python_class.write_function_call(
                'test_function', flag_var=flag_var,
                inputs=inputs, outputs=outputs,
                outputs_in_inputs=outputs_in_inputs)
            run_generated_code(lines,
                               function_definitions=definition)
        return write_function_def_w

    def test_write_function_def(self, python_class, write_function_def,
                                testing_options):
        r"""Test writing and running a function definition."""
        if python_class.function_param is None:
            with pytest.raises(NotImplementedError):
                python_class.write_function_def(None)
        else:
            for kws in testing_options.get('write_function_def_params', []):
                write_function_def(**kws)
            
    def test_write_if_block(self, python_class, run_generated_code):
        r"""Test writing an if block."""
        if python_class.function_param is None:
            with pytest.raises(NotImplementedError):
                python_class.write_if_block(None, None)
        else:
            lines = []
            if 'declare' in python_class.function_param:
                lines += python_class.write_declaration(
                    {'name': 'x', 'type': 'integer'})
            cond = [python_class.function_param['true'],
                    python_class.function_param['false']]
            block_contents = [
                python_class.function_param['assign'].format(
                    name='x', value='1'),
                python_class.function_param['assign'].format(
                    name='x', value='2')]
            else_contents = python_class.function_param['assign'].format(
                name='x', value='-1')
            lines += python_class.write_if_block(
                cond, block_contents,
                else_block_contents=else_contents)
            run_generated_code(lines)

    def test_write_for_loop(self, python_class, run_generated_code):
        r"""Test writing a for loop."""
        if python_class.function_param is None:
            with pytest.raises(NotImplementedError):
                python_class.write_for_loop(None, None, None, None)
        else:
            lines = []
            if 'declare' in python_class.function_param:
                lines += python_class.write_declaration(
                    {'name': 'i', 'type': 'integer'})
                lines += python_class.write_declaration(
                    {'name': 'x', 'type': 'integer'})
            loop_contents = python_class.function_param['assign'].format(
                name='x', value='i')
            lines += python_class.write_for_loop('i', 1, 2, loop_contents)
            run_generated_code(lines)

    def test_write_while_loop(self, python_class, run_generated_code):
        r"""Test writing a while loop."""
        if python_class.function_param is None:
            with pytest.raises(NotImplementedError):
                python_class.write_while_loop(None, None)
        else:
            lines = []
            cond = python_class.function_param['true']
            loop_contents = python_class.function_param.get('break', 'break')
            lines += python_class.write_while_loop(cond, loop_contents)
            run_generated_code(lines)

    def test_write_try_except(self, python_class, run_generated_code,
                              testing_options):
        r"""Test writing a try/except block."""
        if (((python_class.function_param is None)
             or ('try_begin' not in python_class.function_param))):
            with pytest.raises(NotImplementedError):
                python_class.write_try_except(None, None)
        else:
            lines = []
            try_contents = python_class.function_param['error'].format(
                error_msg='Dummy error')
            except_contents = python_class.function_param['print'].format(
                message='Dummy message')
            lines += python_class.write_try_except(
                try_contents, except_contents,
                **testing_options.get('write_try_except_kwargs', {}))
            run_generated_code(lines)

    def test_cleanup_dependencies(self, python_class):
        r"""Test cleanup_dependencies method."""
        # Run twice to ensure things work even if it has been cleand up
        python_class.cleanup_dependencies()
        python_class.cleanup_dependencies()

    def test_split_line(self, python_class, testing_options):
        r"""Test split_line."""
        if python_class.function_param is None:
            return
        for line, kwargs, splits in testing_options.get('split_lines', []):
            assert(python_class.split_line(line, **kwargs) == splits)

    def test_install_model_dependencies(self, python_class, testing_options):
        r"""Test install_model_dependencies."""
        deps = testing_options.get('deps', [])
        python_class.install_model_dependencies(deps, always_yes=True)
        with pytest.raises(NotImplementedError):
            python_class.install_dependency(
                'invalid', package_manager='invalid')
