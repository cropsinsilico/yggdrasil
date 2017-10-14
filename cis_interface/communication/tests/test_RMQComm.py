from cis_interface.communication.tests import test_CommBase as parent

    
class TestRMQComm(parent.TestCommBase):
    r"""Test for RMQComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestRMQComm, self).__init__(*args, **kwargs)
        self.comm = 'RMQComm'
        self.attr_list += ['connection', 'channel']
