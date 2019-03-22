import yggdrasil.drivers.tests.test_InterpretedModelDriver as parent


class TestPythonModelParam(parent.TestInterpretedModelParam):
    r"""Test parameters for PythonModelDriver."""

    driver = "PythonModelDriver"


class TestPythonModelDriver(TestPythonModelParam,
                            parent.TestInterpretedModelDriver):
    r"""Test runner for PythonModelDriver."""
    pass


class TestPythonModelDriverNoStart(TestPythonModelParam,
                                   parent.TestInterpretedModelDriverNoStart):
    r"""Test runner for PythonModelDriver without start."""
    pass
