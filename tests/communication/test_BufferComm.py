from yggdrasil.communication import BufferComm


def test_LockedBuffer_clear(wait_on_function):
    r"""Test the clear method of the LockedBuffer class."""
    x = BufferComm.LockedBuffer()
    x.append('test')
    wait_on_function(lambda: not x.empty())
    x.clear()
    assert(len(x) == 0)


def test_LockedBuffer_pop():
    r"""Test the pop method of the LockedBuffer class."""
    x = BufferComm.LockedBuffer()
    assert(x.pop(default='hello') == 'hello')
