from cis_interface.drivers.tests import test_CommDriver as parent


class TestRMQAsyncCommParam(parent.TestCommParam):
    r"""Test parameters for the RMQAsyncCommDriver class."""
    def __init__(self, *args, **kwargs):
        super(TestRMQAsyncCommParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQAsyncCommDriver'
        self.comm_name = 'RMQAsyncComm'
    

class TestRMQAsyncCommDriverNoStart(TestRMQAsyncCommParam,
                                    parent.TestCommDriverNoStart):
    r"""Test class for the RMQAsyncCommDriver class without start."""
    pass


class TestRMQAsyncCommDriver(TestRMQAsyncCommParam, parent.TestCommDriver):
    r"""Test class for the RMQAsyncCommDriver class."""
    pass
