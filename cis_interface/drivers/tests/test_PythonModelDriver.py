from cis_interface.tests import scripts
import cis_interface.drivers.tests.test_ModelDriver as parent


class TestPythonModelParam(parent.TestModelParam):
    r"""Test parameters for PythonModelDriver.

    Attributes (in addition to parent class's):
        -

    """

    def __init__(self, *args, **kwargs):
        super(TestPythonModelParam, self).__init__(*args, **kwargs)
        self.driver = "PythonModelDriver"
        self.args = scripts["python"]


class TestPythonModelDriver(TestPythonModelParam, parent.TestModelDriver):
    r"""Test runner for PythonModelDriver.

    Attributes (in addition to parent class's):
        -

    """
    pass


class TestPythonModelDriverNoStart(TestPythonModelParam,
                                   parent.TestModelDriverNoStart):
    r"""Test runner for PythonModelDriver without start.

    Attributes (in addition to parent class's):
        -

    """
    pass
