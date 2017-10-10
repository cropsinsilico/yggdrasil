from cis_interface.drivers.tests import test_CommDriver as parent


class TestRPCCommParam(parent.TestCommParam):
    r"""Test parameters for the RPCCommDriver class.

    Attributes:
        -

    """
    def __init__(self, *args, **kwargs):
        super(TestRPCCommParam, self).__init__(*args, **kwargs)
        self.driver = 'RPCCommDriver'
        self.comm_name = 'RPCComm'
    

class TestRPCCommDriverNoStart(TestRPCCommParam, parent.TestCommDriverNoStart):
    r"""Test class for the RPCCommDriver class without start.

    Attributes (in addition to parent class's):
        -

    """
    pass


class TestRPCCommDriver(TestRPCCommParam, parent.TestCommDriver):
    r"""Test class for the RPCCommDriver class.

    Attributes (in addition to parent class's):
        -

    """
    pass
