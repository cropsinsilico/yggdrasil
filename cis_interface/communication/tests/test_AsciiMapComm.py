from cis_interface.communication.tests import test_FileComm as parent


class TestAsciiMapComm(parent.TestFileComm):
    r"""Test for AsciiMapComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestAsciiMapComm, self).__init__(*args, **kwargs)
        self.comm = 'AsciiMapComm'
