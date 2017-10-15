from cis_interface.drivers.tests import test_CommDriver as parent


class TestRMQCommParam(parent.TestCommParam):
    r"""Test parameters for the RMQCommDriver class.

    Attributes:
        -

    """
    def __init__(self, *args, **kwargs):
        super(TestRMQCommParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQCommDriver'
        self.comm_name = 'RMQComm'
    

class TestRMQCommDriverNoStart(TestRMQCommParam, parent.TestCommDriverNoStart):
    r"""Test class for the RMQCommDriver class without start.

    Attributes (in addition to parent class's):
        -

    """
    pass


class TestRMQCommDriver(TestRMQCommParam, parent.TestCommDriver):
    r"""Test class for the RMQCommDriver class.

    Attributes (in addition to parent class's):
        -

    """
    pass
