import os
import copy
import unittest
from yggdrasil.tests import assert_raises, scripts
from yggdrasil.drivers.ModelDriver import ModelDriver, remove_product
from yggdrasil.drivers.CompiledModelDriver import CompiledModelDriver
from yggdrasil.drivers.InterpretedModelDriver import InterpretedModelDriver
import yggdrasil.drivers.tests.test_Driver as parent


def test_remove_product():
    r"""Test remove_product."""
    test_file = os.path.join(os.path.dirname(__file__), 'remove_product_test.py')
    with open(test_file, 'w') as fd:
        fd.write('print(\'hello\')')
    try:
        assert_raises(RuntimeError, remove_product, test_file,
                      check_for_source=True)
        assert_raises(RuntimeError, remove_product, os.path.dirname(test_file),
                      check_for_source=True)
    finally:
        os.remove(test_file)


def test_ModelDriver_implementation():
    r"""Test that NotImplementedError raised for base class."""
    assert_raises(NotImplementedError, ModelDriver.language_executable)
    assert_raises(NotImplementedError, ModelDriver.executable_command, None)
    assert_raises(NotImplementedError, ModelDriver.is_library_installed, None)
    assert_raises(NotImplementedError, CompiledModelDriver.get_tool, 'compiler')
    assert_raises(NotImplementedError, InterpretedModelDriver.get_interpreter)

    
class TestModelParam(parent.TestParam):
    r"""Test parameters for basic ModelDriver class."""

    driver = 'ModelDriver'
    
    def __init__(self, *args, **kwargs):
        super(TestModelParam, self).__init__(*args, **kwargs)
        self.attr_list += ['args', 'process', 'queue', 'queue_thread',
                           'is_server', 'client_of',
                           'event_process_kill_called',
                           'event_process_kill_complete',
                           'with_strace', 'strace_flags',
                           'with_valgrind', 'valgrind_flags',
                           'model_index', 'model_file', 'model_args',
                           'products', 'overwrite']
        self.src = None
        if self.import_cls.language is not None:
            self.src = scripts[self.import_cls.language]
            if not isinstance(self.src, list):
                self.src = [self.src]
        if self.src is not None:
            self.args = copy.deepcopy(self.src)

    def tests_on_not_installed(self):
        r"""Tests for when the driver is not installed."""
        if self.import_cls.is_installed():
            raise unittest.SkipTest("'%s' installed."
                                    % self.import_cls.language)

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        cls._flag_tests_on_not_installed = False
        super(TestModelParam, cls).setUpClass(*args, **kwargs)

    def setup(self, *args, **kwargs):
        if self.import_cls.language is None:
            raise unittest.SkipTest("Driver dosn't have language.")
        if not self.import_cls.is_installed():
            if not self.__class__._flag_tests_on_not_installed:
                if not self.skip_init:
                    self.assert_raises(RuntimeError,
                                       super(TestModelParam, self).setup,
                                       *args, **kwargs)
                self.tests_on_not_installed()
                self.__class__._flag_tests_on_not_installed = True
            raise unittest.SkipTest("'%s' not installed."
                                    % self.import_cls.language)
        super(TestModelParam, self).setup(*args, **kwargs)


class TestModelDriverNoInit(TestModelParam, parent.TestDriverNoInit):
    r"""Test runner for ModelDriver class without creating an instance."""

    def tests_on_not_installed(self):
        r"""Tests for when the driver is not installed."""
        super(TestModelDriverNoInit, self).tests_on_not_installed()
        self.test_comm_installed()
        self.test_write_if_block()
        self.test_write_for_loop()
        self.test_write_while_loop()
        self.test_write_try_except()

    def test_is_installed(self):
        r"""Assert that the tested model driver is installed."""
        assert(self.import_cls.is_installed())

    def test_comm_installed(self):
        r"""Tests for getting installed comm while skipping config."""
        self.assert_equal(self.import_cls.is_comm_installed(),
                          self.import_cls.is_comm_installed(skip_config=True))
        self.assert_equal(self.import_cls.is_comm_installed(commtype='invalid',
                                                            skip_config=True),
                          False)
        
    def test_language_version(self):
        r"""Test language version."""
        assert(self.import_cls.language_version())

    # Tests for code generation
    def run_generated_code(self, lines):
        r"""Write and run generated code."""
        if not self.import_cls.is_installed():
            return
        # Write code to a file
        self.import_cls.run_code(lines)
            
    def test_write_executable(self):
        r"""Test writing an executable."""
        if self.import_cls.function_param is None:
            self.assert_raises(NotImplementedError,
                               self.import_cls.write_executable,
                               None)
        else:
            lines1 = self.import_cls.write_executable('dummy',
                                                      prefix='dummy',
                                                      suffix='dummy')
            lines2 = self.import_cls.write_executable(lines1)
            self.assert_equal(lines1, lines2)
            # Don't run this because it is invalid

    def test_error_code(self):
        r"""Test that error is raised when code generates one."""
        if (((not self.import_cls.is_installed())
             or (self.import_cls.function_param is None))):
            return
        error_msg = 'Test error'
        lines = [self.import_cls.function_param['error'].format(error_msg=error_msg)]
        assert_raises(RuntimeError, self.import_cls.run_code, lines)

    def test_write_if_block(self):
        r"""Test writing an if block."""
        if self.import_cls.function_param is None:
            self.assert_raises(NotImplementedError, self.import_cls.write_if_block,
                               None, None)
        else:
            lines = []
            if 'declare' in self.import_cls.function_param:
                lines.append(self.import_cls.function_param['declare'].format(
                    type='int', name='x'))
            cond = self.import_cls.function_param['true']
            block_contents = self.import_cls.function_param['assign'].format(
                name='x', value='1')
            lines += self.import_cls.write_if_block(cond, block_contents)
            self.run_generated_code(lines)

    def test_write_for_loop(self):
        r"""Test writing a for loop."""
        if self.import_cls.function_param is None:
            self.assert_raises(NotImplementedError, self.import_cls.write_for_loop,
                               None, None, None, None)
        else:
            lines = []
            if 'declare' in self.import_cls.function_param:
                lines.append(self.import_cls.function_param['declare'].format(
                    type='int', name='i'))
                lines.append(self.import_cls.function_param['declare'].format(
                    type='int', name='x'))
            loop_contents = self.import_cls.function_param['assign'].format(
                name='x', value='i')
            lines += self.import_cls.write_for_loop('i', 0, 1, loop_contents)
            self.run_generated_code(lines)

    def test_write_while_loop(self):
        r"""Test writing a while loop."""
        if self.import_cls.function_param is None:
            self.assert_raises(NotImplementedError, self.import_cls.write_while_loop,
                               None, None)
        else:
            lines = []
            cond = self.import_cls.function_param['true']
            loop_contents = self.import_cls.function_param.get('break', 'break')
            lines += self.import_cls.write_while_loop(cond, loop_contents)
            self.run_generated_code(lines)

    def test_write_try_except(self, **kwargs):
        r"""Test writing a try/except block."""
        if self.import_cls.function_param is None:
            self.assert_raises(NotImplementedError, self.import_cls.write_try_except,
                               None, None)
        else:
            lines = []
            try_contents = self.import_cls.function_param['error'].format(
                error_msg='Dummy error')
            except_contents = self.import_cls.function_param['print'].format(
                message='Dummy message')
            lines += self.import_cls.write_try_except(try_contents,
                                                      except_contents, **kwargs)
            self.run_generated_code(lines)
    

class TestModelDriverNoStart(TestModelParam, parent.TestDriverNoStart):
    r"""Test runner for basic ModelDriver class."""
    pass


class TestModelDriver(TestModelParam, parent.TestDriver):
    r"""Test runner for basic ModelDriver class."""
    pass
