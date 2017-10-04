from cis_interface.communication.tests import test_CommBase as parent


class TestIPCComm(parent.TestCommBase):
    r"""Test for IPCComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestIPCComm, self).__init__(*args, **kwargs)
        self.comm = 'IPCComm'
        self.attr_list += ['q']
