import tempfile
from yggdrasil.tests import generate_component_tests, assert_equal, assert_raises
from yggdrasil.communication import open_file_comm
from yggdrasil.communication.tests.test_FileComm import TestFileComm


generate_component_tests('file', TestFileComm, globals(), __file__,
                         class_attr='comm')


def test_open_file_comm():
    r"""Test file comm context manager."""
    with tempfile.NamedTemporaryFile() as fd:
        fname = fd.name
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
        assert_equal(res, 2 * msg)
    with assert_raises(ValueError):
        with open_file_comm(fname, 'invalid') as comm:  # pragma: debug
            pass


__all__ = []
