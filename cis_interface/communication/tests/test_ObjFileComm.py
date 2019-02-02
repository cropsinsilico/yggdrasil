from cis_interface.communication.tests import test_PlyFileComm as parent


class TestObjFileComm(parent.TestPlyFileComm):
    r"""Test for ObjFileComm communication class."""

    comm = 'ObjFileComm'
