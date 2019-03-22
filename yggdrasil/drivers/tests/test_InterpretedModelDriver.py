import copy
from yggdrasil.drivers.tests import test_ModelDriver as parent


class TestInterpretedModelParam(parent.TestModelParam):
    r"""Test parameters for basic InterpretedModelDriver class."""

    driver = 'InterpretedModelDriver'

    def __init__(self, *args, **kwargs):
        super(TestInterpretedModelParam, self).__init__(*args, **kwargs)
        if self.src is not None:
            self.args = copy.deepcopy(self.src)


class TestInterpretedModelDriver(TestInterpretedModelParam,
                                 parent.TestModelDriver):
    r"""Test runner for InterpretedModelDriver."""
    pass


class TestInterpretedModelDriverNoStart(TestInterpretedModelParam,
                                        parent.TestModelDriverNoStart):
    r"""Test runner for InterpretedModelDriver without start."""
    pass
