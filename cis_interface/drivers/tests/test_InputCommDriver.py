from cis_interface.drivers.tests import test_CommDriver as parent


class TestInputCommParam(parent.TestCommParam):
    r"""Test parameters for the InputCommDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestInputCommParam, self).__init__(*args, **kwargs)
        self.driver = 'InputCommDriver'


class TestInputCommDriverNoStart(TestInputCommParam,
                                 parent.TestCommDriverNoStart):
    r"""Test class for the InputCommDriver class without start."""
    pass


class TestInputCommDriver(TestInputCommParam, parent.TestCommDriver):
    r"""Test class for the InputCommDriver class."""
    pass
