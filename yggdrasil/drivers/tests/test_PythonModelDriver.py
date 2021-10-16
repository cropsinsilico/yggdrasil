import yggdrasil.drivers.tests.test_InterpretedModelDriver as parent


class TestPythonModelParam(parent.TestInterpretedModelParam):
    r"""Test parameters for PythonModelDriver."""

    driver = "PythonModelDriver"


class TestPythonModelDriverNoInit(TestPythonModelParam,
                                  parent.TestInterpretedModelDriverNoInit):
    r"""Test runner for PythonModelDriver without init."""

    def test_install_model_dependencies(self, deps=None):
        r"""Test install_model_dependencies."""
        if deps is None:
            deps = [{'package': 'numpy', 'arguments': '-v'},
                    'requests', 'pyyaml']
        super(TestPythonModelDriverNoInit, self).test_install_model_dependencies(
            deps=deps)
        

class TestPythonModelDriverNoStart(TestPythonModelParam,
                                   parent.TestInterpretedModelDriverNoStart):
    r"""Test runner for PythonModelDriver without start."""
    pass


class TestPythonModelDriver(TestPythonModelParam,
                            parent.TestInterpretedModelDriver):
    r"""Test runner for PythonModelDriver."""
    pass
