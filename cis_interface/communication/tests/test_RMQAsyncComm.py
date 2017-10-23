from cis_interface.communication.tests import test_RMQComm as parent

    
class TestRMQAsyncComm(parent.TestRMQComm):
    r"""Test for RMQAsyncComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestRMQAsyncComm, self).__init__(*args, **kwargs)
        self.comm = 'RMQAsyncComm'
        self.attr_list += ['times_connected']
