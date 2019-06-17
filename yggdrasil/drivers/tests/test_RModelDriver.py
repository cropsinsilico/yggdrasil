import yggdrasil.drivers.tests.test_InterpretedModelDriver as parent


class TestRModelParam(parent.TestInterpretedModelParam):
    r"""Test parameters for RModelDriver."""

    driver = "RModelDriver"


class TestRModelDriverNoInit(TestRModelParam,
                             parent.TestInterpretedModelDriverNoInit):
    r"""Test runner for RModelDriver without init."""
    pass


class TestRModelDriverNoStart(TestRModelParam,
                              parent.TestInterpretedModelDriverNoStart):
    r"""Test runner for RModelDriver without start."""
    pass


class TestRModelDriver(TestRModelParam,
                       parent.TestInterpretedModelDriver):
    r"""Test runner for RModelDriver."""
    pass
