import pytest
from tests.communication.test_FileComm import TestFileComm as base_class


class TestAsciiFileComm(base_class):
    r"""Test for AsciiFileComm communication class."""

    @pytest.fixture(scope="class", autouse=True)
    def filetype(self):
        r"""Communicator type being tested."""
        return "ascii"

    def test_send_recv_comment(self, send_comm, recv_comm, testing_options):
        r"""Test send/recv with commented message."""
        msg_send = send_comm.serializer.comment + testing_options['msg']
        flag = send_comm.send(msg_send)
        assert(flag)
        flag, msg_recv = recv_comm.recv()
        assert(not flag)
        assert(msg_recv == recv_comm.eof_msg)
