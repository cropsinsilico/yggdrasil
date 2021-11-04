import os
import uuid
import pytest
from yggdrasil.communication import open_file_comm


def test_open_file_comm():
    r"""Test file comm context manager."""
    fname = os.path.join(os.path.dirname(__file__),
                         '%s.txt' % str(uuid.uuid4()))
    try:
        msg = b'Test message'
        with open_file_comm(fname, 'w') as comm:
            flag = comm.send(msg)
            assert(flag)
        with open_file_comm(fname, 'a') as comm:
            flag = comm.send(msg)
            assert(flag)
        with open_file_comm(fname, 'r') as comm:
            flag, res = comm.recv()
            assert(flag)
        assert(res == 2 * msg)
    finally:
        if os.path.isfile(fname):
            os.remove(fname)
    with pytest.raises(ValueError):
        with open_file_comm(fname, 'invalid') as comm:  # pragma: debug
            pass


__all__ = []
