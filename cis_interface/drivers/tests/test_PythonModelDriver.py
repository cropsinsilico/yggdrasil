from cis_interface.tests import scripts
import test_ModelDriver as parent


class TestPythonModelDriver(parent.TestModelDriver):
    r"""Test runner for PythonModelDriver."""

    def __init__(self):
        super(TestPythonModelDriver, self).__init__()
        self.driver = "PythonModelDriver"
        self.args = scripts["python"]
