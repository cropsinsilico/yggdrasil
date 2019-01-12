from cis_interface.communication.tests import test_PlyFileComm as parent


class TestObjFileComm(parent.TestPlyFileComm):
    r"""Test for ObjFileComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestObjFileComm, self).__init__(*args, **kwargs)
        self.comm = 'ObjFileComm'
