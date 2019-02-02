from cis_interface.communication.tests import test_FileComm as parent


class TestYAMLFileComm(parent.TestFileComm):
    r"""Test for YAMLFileComm communication class."""

    comm = 'YAMLFileComm'
