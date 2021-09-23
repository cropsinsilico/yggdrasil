from yggdrasil import tools
from yggdrasil.tests import assert_equal
from yggdrasil.communication import BufferComm
from yggdrasil.communication.tests import test_CommBase


def test_LockedBuffer_clear():
    r"""Test the clear method of the LockedBuffer class."""
    x = BufferComm.LockedBuffer()
    x.append('test')
    while x.empty():
        tools.sleep(0.1)
    assert(not x.empty())
    x.clear()
    assert_equal(len(x), 0)


def test_LockedBuffer_pop():
    r"""Test the pop method of the LockedBuffer class."""
    x = BufferComm.LockedBuffer()
    assert_equal(x.pop(default='hello'), 'hello')


class TestBufferComm(test_CommBase.TestCommBase):
    r"""Tests for BufferComm communication class."""

    comm = 'BufferComm'
    
    test_error_name = None
