from cis_interface.drivers.tests import test_CommDriver as parent


class TestIOParam(parent.TestCommParam):
    r"""Test parameters for the IODriver class.

    Attributes (in addition to parent class's):
        -

    """
    def __init__(self, *args, **kwargs):
        super(TestIOParam, self).__init__(*args, **kwargs)
        self.driver = 'IODriver'
        self.args = '_TEST'
        self.timeout = 20.0

    
class TestIODriverNoStart(TestIOParam, parent.TestCommDriverNoStart):
    r"""Test class for the IODriver class without start.

    Attributes (in addition to parent class's):
        -

    """
    pass


class TestIODriver(TestIOParam, parent.TestCommDriver):
    r"""Test class for the IODriver class.

    Attributes (in addition to parent class's):
        -

    """
    pass
