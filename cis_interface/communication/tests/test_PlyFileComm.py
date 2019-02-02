from cis_interface.communication.tests import test_FileComm as parent


class TestPlyFileComm(parent.TestFileComm):
    r"""Test for PlyFileComm communication class."""

    comm = 'PlyFileComm'
