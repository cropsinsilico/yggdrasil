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
    pass
