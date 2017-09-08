import nose.tools as nt
import cis_interface.drivers.tests.test_RMQDriver as parent1
from cis_interface.drivers.tests.test_IODriver import IOInfo


class TestRMQInputParam(parent1.TestRMQParam, IOInfo):
    r"""Test parameters for RMQInputDriver.

    Attributes (in addition to parent class's):
        -

    """

    def __init__(self, *args, **kwargs):
        super(TestRMQInputParam, self).__init__(*args, **kwargs)
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

    def test_early_close(self):
        r"""Test early deletion of message queue."""
        self.instance.close_queue()

    # Disabled so that test message is not read by mistake
    def test_purge(self):
        r"""Test purge of queue."""
        pass

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
