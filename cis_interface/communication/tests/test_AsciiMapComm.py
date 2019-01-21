from cis_interface.communication.tests import test_FileComm as parent


class TestAsciiMapComm(parent.TestFileComm):
    r"""Test for AsciiMapComm communication class."""

    comm = 'AsciiMapComm'
