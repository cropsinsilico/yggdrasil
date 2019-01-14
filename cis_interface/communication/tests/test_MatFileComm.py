from cis_interface.communication.tests import test_FileComm as parent


class TestMatFileComm(parent.TestFileComm):
    r"""Test for MatFileComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestMatFileComm, self).__init__(*args, **kwargs)
        self.comm = 'MatFileComm'
