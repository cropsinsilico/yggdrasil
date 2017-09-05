import nose.tools as nt
import test_RMQDriver as parent1
from test_IODriver import IOInfo


class TestRMQInputParam(parent1.TestRMQParam, IOInfo):
    r"""Test parameters for RMQInputDriver.

    Attributes (in addition to parent class's):
        -

    """

    def __init__(self):
        super(TestRMQInputParam, self).__init__()
        self.driver = 'RMQInputDriver'
        self.args = 'test'

        
class TestRMQInputDriverNoStart(TestRMQInputParam,
                                parent1.TestRMQDriverNoStart):
    r"""Test runner for RMQInputDriver without start.

    Attributes (in addition to parent class's):
        -

    """
    pass


class TestRMQInputDriver(TestRMQInputParam, parent1.TestRMQDriver):
    r"""Test runner for RMQInputDriver.

    Attributes (in addition to parent class's):
        -

    """

    def test_RMQ_recv(self):
        r"""Receive a small message from AMQP server."""
        self.instance.rmq_send(self.msg_short)
        self.instance.sleep(0.1)
        msg_recv = self.instance.recv_wait(timeout=3)
        nt.assert_equal(msg_recv, self.msg_short)

    def test_RMQ_recv_nolimit(self):
        r"""Receive a large message from AMQP server."""
        self.instance.rmq_send_nolimit(self.msg_long)
        self.instance.sleep(0.1)
        msg_recv = self.instance.recv_wait_nolimit(timeout=3)
        nt.assert_equal(msg_recv, self.msg_long)
