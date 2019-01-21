from yggdrasil.communication.tests import test_FileComm as parent


class TestPickleFileComm(parent.TestFileComm):
    r"""Test for PickleFileComm communication class."""

    comm = 'PickleFileComm'
