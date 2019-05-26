from yggdrasil.drivers.tests import test_ModelDriver as parent


class TestInterpretedModelParam(parent.TestModelParam):
    r"""Test parameters for basic InterpretedModelDriver class."""

    driver = 'InterpretedModelDriver'


class TestInterpretedModelDriver(TestInterpretedModelParam,
                                 parent.TestModelDriver):
    r"""Test runner for InterpretedModelDriver."""
    pass


class TestInterpretedModelDriverNoStart(TestInterpretedModelParam,
                                        parent.TestModelDriverNoStart):
    r"""Test runner for InterpretedModelDriver without start."""
    
    def test_invalid_executable(self):
        r"""Test error raise for invalid exec_type."""
        self.assert_raises(ValueError, self.import_cls.executable_command, [],
                           exec_type='invalid')
