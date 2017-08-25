import nose.tools as nt
import os
import test_RMQConnection as parent


class TestRMQInputDriver(parent.TestRMQConnection):
    r"""Test runner for RMQInputDriver."""

    def __init__(self):
        super(TestRMQInputDriver, self).__init__()
        self.driver = 'RMQInputDriver'
        self.args = 'test'

    def test_RMQ_recv(self):
        r"""Receive a small message from AMQP server."""
        self.instance.rmq_send(self.msg_short)
        msg_recv = self.instance.recv_wait()
        nt.assert_equal(msg_recv, self.msg_short)

    def test_RMQ_recv_nolimit(self):
        r"""Receive a large message from AMQP server."""
        self.instance.rmq_send_nolimit(self.msg_long)
        msg_recv = self.instance.recv_wait_nolimit()
        nt.assert_equal(msg_recv, self.msg_long)

