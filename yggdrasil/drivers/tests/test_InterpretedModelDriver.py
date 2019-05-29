from yggdrasil.drivers.tests import test_ModelDriver as parent


class TestInterpretedModelParam(parent.TestModelParam):
    r"""Test parameters for basic InterpretedModelDriver class."""

    driver = 'InterpretedModelDriver'


class TestInterpretedModelDriver(TestInterpretedModelParam,
                                 parent.TestModelDriver):
    r"""Test runner for InterpretedModelDriver."""
    pass


class TestInterpretedModelDriverNoInit(TestInterpretedModelParam,
                                       parent.TestModelDriverNoInit):
    r"""Test runner for InterpretedModelDriver without init."""

    def test_executable_command(self):
        r"""Test error raise for invalid exec_type."""
        self.assert_raises(ValueError, self.import_cls.executable_command, [],
                           exec_type='invalid')

        
class TestInterpretedModelDriverNoStart(TestInterpretedModelParam,
                                        parent.TestModelDriverNoStart):
    r"""Test runner for InterpretedModelDriver without start."""
    pass
