from cis_interface.drivers.tests import test_CommDriver as parent


class TestIPCCommParam(parent.TestCommParam):
    r"""Test parameters for the IPCCommDriver class.

    Attributes:
        -

    """
    def __init__(self, *args, **kwargs):
        super(TestIPCCommParam, self).__init__(*args, **kwargs)
        self.driver = 'IPCCommDriver'
        self.comm_name = 'IPCComm'
    

class TestIPCCommDriverNoStart(TestIPCCommParam, parent.TestCommDriverNoStart):
    r"""Test class for the IPCCommDriver class without start.

    Attributes (in addition to parent class's):
        -

    """
    pass


class TestIPCCommDriver(TestIPCCommParam, parent.TestCommDriver):
    r"""Test class for the IPCCommDriver class.

    Attributes (in addition to parent class's):
        -

    """
    pass
