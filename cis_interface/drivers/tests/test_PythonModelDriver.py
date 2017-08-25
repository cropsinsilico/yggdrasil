import test_ModelDriver as parent


class TestPythonModelDriver(parent.TestModelDriver):
    r"""Test runner for PythonModelDriver."""

    def __init__(self):
        super(TestPythonModelDriver, self).__init__()
        self.driver = "PythonModelDriver"
        self.args = "python_model.py"
