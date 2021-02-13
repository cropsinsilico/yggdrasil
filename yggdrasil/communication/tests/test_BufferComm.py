from yggdrasil.communication.tests import test_CommBase


class TestBufferComm(test_CommBase.TestCommBase):
    r"""Tests for BufferComm communication class."""

    comm = 'BufferComm'
    
    test_error_name = None
