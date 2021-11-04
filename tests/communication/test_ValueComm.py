import pytest
from yggdrasil.communication import new_comm
from tests.communication.test_CommBase import BaseComm as base_class


class TestValueComm(base_class):
    r"""Test for ValueComm communication class."""

    comm = 'ValueComm'

    @pytest.fixture(scope="class", autouse=True)
    def commtype(self):
        r"""Communicator type being tested."""
        return "value"

    def create_recv_comm(self, name, commtype, use_async, testing_options,
                         **kwargs):
        r"""Create a recv comm."""
        kws = dict(commtype=commtype, reverse_names=True,
                   direction='recv', use_async=use_async)
        kws.update(testing_options['kwargs'])
        kws.update(kwargs)
        x = new_comm(name, **kws)
        assert(x.is_open)
        return x

    @pytest.fixture(scope="class")
    def global_send_comm(self):
        r"""Communicator for sending messages."""
        return None

    @pytest.fixture(scope="class")
    def global_recv_comm(self):
        r"""Communicator for receiving messages."""
        return None

    @pytest.fixture
    def send_comm(self):
        r"""Communicator for sending messages."""
        return None

    @pytest.fixture
    def recv_comm(self, name, commtype, use_async, testing_options,
                  sleep_after_connect, close_comm):
        r"""Communicator for receiving messages."""
        recv_comm = self.create_recv_comm(name, commtype, use_async,
                                          testing_options)
        if sleep_after_connect:
            recv_comm.sleep()
        yield recv_comm
        close_comm(recv_comm)

    @pytest.fixture(scope="class")
    def maxMsgSize(self):
        r"""int: Maximum message size."""
        return 0

    def test_send_recv(self, recv_comm, testing_options, use_async, timeout,
                       map_sent2recv, wait_on_function):
        r"""Test send/recv of a small message."""
        n_recv = testing_options['kwargs']['count']
        msg_recv = testing_options['msg']
        if use_async:
            wait_on_function(lambda: recv_comm.n_msg_recv > 0)
            assert(recv_comm.n_msg_recv > 0)
        else:
            assert(recv_comm.n_msg_recv == n_recv)
        # Wait for messages to be received
        for i in range(n_recv):
            flag, msg_recv0 = recv_comm.recv(timeout)
            assert(flag)
            assert(msg_recv0 == map_sent2recv(msg_recv))
        # Receive after empty
        assert(recv_comm.is_open)
        flag, msg_recv0 = recv_comm.recv(timeout)
        assert(not flag)
        assert(recv_comm.is_eof(msg_recv0))
        # assert(flag)
        # assert(recv_comm.is_empty_recv(msg_recv0))
        # Confirm recept of messages
        recv_comm.wait_for_confirm(timeout=timeout)
        assert(recv_comm.is_confirmed)
        recv_comm.confirm(noblock=True)
        assert(recv_comm.n_msg_recv == 0)

    def test_send_recv_after_close(self, recv_comm, use_async):
        r"""Test that opening twice dosn't cause errors and that send/recv after
        close returns false."""
        recv_comm.open()
        recv_comm.close()
        assert(recv_comm.is_closed)
        flag, msg_recv = recv_comm.recv()
        if not use_async:
            assert(not flag)
        with pytest.raises(RuntimeError):
            recv_comm.send(None)

    def test_purge(self, recv_comm, wait_on_function):
        r"""Test purging messages from the comm."""
        wait_on_function(lambda: recv_comm.n_msg > 0)
        assert(recv_comm.n_msg > 0)
        recv_comm.purge()
        assert(recv_comm.n_msg == 0)
        recv_comm.close()
        recv_comm.purge()
