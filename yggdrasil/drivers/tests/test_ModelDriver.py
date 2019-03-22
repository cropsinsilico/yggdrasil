import unittest
from yggdrasil.tests import assert_raises, scripts
from yggdrasil.drivers.ModelDriver import ModelDriver
from yggdrasil.drivers.CompiledModelDriver import CompiledModelDriver
from yggdrasil.drivers.InterpretedModelDriver import InterpretedModelDriver
import yggdrasil.drivers.tests.test_Driver as parent


def test_ModelDriver_implementation():
    r"""Test that NotImplementedError raised for base class."""
    assert_raises(NotImplementedError, ModelDriver.language_executable)
    assert_raises(NotImplementedError, ModelDriver.executable_command, None)
    assert_raises(NotImplementedError, CompiledModelDriver.compiler)
    assert_raises(NotImplementedError, InterpretedModelDriver.interpreter)

    
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

    def tests_on_not_installed(self):
        r"""Tests for when the driver is not installed."""
        if self.import_cls.is_installed():
            raise unittest.SkipTest("'%s' installed."
                                    % self.import_cls.language)

    def setup(self, *args, **kwargs):
        if self.import_cls.language is None:
            raise unittest.SkipTest("Driver dosn't have language.")
        if not self.import_cls.is_installed():
            self.assert_raises(RuntimeError, super(TestModelParam, self).setup,
                               *args, **kwargs)
            self.tests_on_not_installed()
            raise unittest.SkipTest("'%s' not installed."
                                    % self.import_cls.language)
        super(TestModelParam, self).setup(*args, **kwargs)
        

class TestModelDriverNoStart(TestModelParam, parent.TestDriverNoStart):
    r"""Test runner for basic ModelDriver class."""

    def test_is_installed(self):
        r"""Assert that the tested model driver is installed."""
        # if self.driver == 'ModelDriver':
        #     assert(not self.import_cls.is_installed())
        # else:
        assert(self.import_cls.is_installed())

    def test_language_version(self):
        r"""Test language version."""
        assert(self.import_cls.language_version())


class TestModelDriver(TestModelParam, parent.TestDriver):
    r"""Test runner for basic ModelDriver class."""
    pass
