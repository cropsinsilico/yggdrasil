import yggdrasil.drivers.tests.test_InterpretedModelDriver as parent


class TestLPyModelParam(parent.TestInterpretedModelParam):
    r"""Test parameters for LPyModelDriver class."""

    driver = 'LPyModelDriver'

        
class TestLPyModelDriverNoStart(TestLPyModelParam,
                                parent.TestInterpretedModelDriverNoStart):
    r"""Test runner for LPyModelDriver class without starting the driver."""
    pass


class TestLPyModelDriver(TestLPyModelParam,
                         parent.TestInterpretedModelDriver):
    r"""Test runner for LPyModelDriver class."""
    pass
