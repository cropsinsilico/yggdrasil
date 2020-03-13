from yggdrasil.communication.tests import test_CommBase


class TestBufferComm(test_CommBase.TestCommBase):
    r"""Tests for BufferComm communication class."""

    comm = 'BufferComm'

    def test_error_name(self):
        r"""Test error on missing address."""
        # Skipped because the name is not used to intialize
        # the address for a buffer
        pass
