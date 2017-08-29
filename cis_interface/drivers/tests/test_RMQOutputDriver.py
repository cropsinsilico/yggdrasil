import nose.tools as nt
import os
from cis_interface import PsiRun
import test_RMQConnection as parent


class TestRMQOutputDriver(parent.TestRMQConnection):
    r"""Test runner for RMQOutputDriver."""

    def __init__(self):
        super(TestRMQOutputDriver, self).__init__()
        self.driver = 'RMQOutputDriver'
        self.args = 'test'

    def setup(self):
        r"""Create a driver instance and start the driver."""
        super(TestRMQOutputDriver, self).setup()
        self.in_rmq = self.create_in_rmq()
        self.in_rmq.start()

    def teardown(self):
        r"""Remove the instance, stoppping it."""
        if hasattr(self, 'in_rmq'):
            self.remove_instance(self.in_rmq)
            delattr(self, 'in_rmq')
        super(TestRMQOutputDriver, self).teardown()

    def create_in_rmq(self):
        r"""Create a new RMQInputDriver instance."""
        inst = PsiRun.create_driver(
            'RMQInputDriver', 'TestRMQInputDriver', self.args,
            namespace=self.namespace, workingDir=self.workingDir)
        return inst

    def test_RMQ_send(self):
        r"""Send a short message to the AMQP server."""
        self.instance.ipc_send(self.msg_short)
        msg_recv = self.in_rmq.recv_wait()
        nt.assert_equal(msg_recv, self.msg_short)

    def test_RMQ_send_nolimit(self):
        r"""Send a long message to the AMQP server."""
        self.instance.ipc_send_nolimit(self.msg_long)
        msg_recv = self.in_rmq.recv_wait_nolimit()
        nt.assert_equal(msg_recv, self.msg_long)
