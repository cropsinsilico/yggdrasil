from cis_interface.communication.tests import test_CommBase as parent

    
class TestRMQComm(parent.TestCommBase):
    r"""Test for RMQComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestRMQComm, self).__init__(*args, **kwargs)
        self.comm = 'RMQComm'
        self.attr_list += ['connection', 'channel']

    def test_double_open(self):
        r"""test that opening/binding twice dosn't cause errors."""
        super(TestRMQComm, self).test_double_open()
        self.send_instance.bind()
        self.recv_instance.bind()
