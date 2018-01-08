from cis_interface.communication.tests import test_FileComm as parent


class TestPickleFileComm(parent.TestFileComm):
    r"""Test for PickleFileComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestPickleFileComm, self).__init__(*args, **kwargs)
        self.comm = 'PickleFileComm'
