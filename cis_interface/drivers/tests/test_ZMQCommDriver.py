from cis_interface.drivers.tests import test_CommDriver as parent


class TestZMQCommParam(parent.TestCommParam):
    r"""Test parameters for the ZMQCommDriver class.

    Attributes:
        -

    """
    def __init__(self, *args, **kwargs):
        super(TestZMQCommParam, self).__init__(*args, **kwargs)
        self.driver = 'ZMQCommDriver'
        self.comm_name = 'ZMQComm'
    

class TestZMQCommDriverNoStart(TestZMQCommParam, parent.TestCommDriverNoStart):
    r"""Test class for the ZMQCommDriver class without start.

    Attributes (in addition to parent class's):
        -

    """
    pass


class TestZMQCommDriver(TestZMQCommParam, parent.TestCommDriver):
    r"""Test class for the ZMQCommDriver class.

    Attributes (in addition to parent class's):
        -

    """
    pass
