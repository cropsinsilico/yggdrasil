from yggdrasil.tests import scripts
import yggdrasil.drivers.tests.test_ModelDriver as parent


class TestPythonModelParam(parent.TestModelParam):
    r"""Test parameters for PythonModelDriver."""

    driver = "PythonModelDriver"
    
    def __init__(self, *args, **kwargs):
        super(TestPythonModelParam, self).__init__(*args, **kwargs)
        self.args = scripts["python"]


class TestPythonModelDriver(TestPythonModelParam, parent.TestModelDriver):
    r"""Test runner for PythonModelDriver."""
    pass


class TestPythonModelDriverNoStart(TestPythonModelParam,
                                   parent.TestModelDriverNoStart):
    r"""Test runner for PythonModelDriver without start."""
    pass
