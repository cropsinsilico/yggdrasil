from cis_interface.drivers.tests import test_CommDriver as parent


class TestOutputCommParam(parent.TestCommParam):
    r"""Test parameters for the OutputCommDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestOutputCommParam, self).__init__(*args, **kwargs)
        self.driver = 'OutputCommDriver'


class TestOutputCommDriverNoStart(TestOutputCommParam,
                                  parent.TestCommDriverNoStart):
    r"""Test class for the OutputCommDriver class without start."""
    pass


class TestOutputCommDriver(TestOutputCommParam, parent.TestCommDriver):
    r"""Test class for the OutputCommDriver class."""
    pass
