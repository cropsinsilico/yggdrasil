from cis_interface.communication.tests import test_FileComm as parent


class TestJSONFileComm(parent.TestFileComm):
    r"""Test for JSONFileComm communication class."""

    comm = 'JSONFileComm'
