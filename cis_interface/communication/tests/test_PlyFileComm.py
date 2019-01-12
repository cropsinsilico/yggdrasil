from cis_interface.communication.tests import test_FileComm as parent


class TestPlyFileComm(parent.TestFileComm):
    r"""Test for PlyFileComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestPlyFileComm, self).__init__(*args, **kwargs)
        self.comm = 'PlyFileComm'
