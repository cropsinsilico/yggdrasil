from yggdrasil.communication.tests import test_FileComm as parent


class TestMatFileComm(parent.TestFileComm):
    r"""Test for MatFileComm communication class."""

    comm = 'MatFileComm'
