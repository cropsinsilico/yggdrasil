import pika
import nose.tools as nt
import test_RMQDriver as parent1
import test_RPCDriver as parent2


class TestRMQServerDriver(parent1.TestRMQDriver, parent2.TestRPCDriver):
    r"""Test class for RMQServerDriver class."""

    def __init__(self):
        super(TestRMQServerDriver, self).__init__()
        self.driver = 'RMQServerDriver'
        self.args = None
        self.attr_list += ['n_clients']

    def test_msg(self):
        r"""Test routing of a message through the IPC & RMQ queues."""
        # Send message to RMQ input & receive from IPC input
        self.instance.channel.basic_publish(
            exchange=self.instance.exchange,
            routing_key=self.instance.queue,
            properties=pika.BasicProperties(reply_to = self.temp_queue),
            body=self.msg_short)
        ipc_msg = self.instance.iipc.recv_wait_nolimit()
        nt.assert_equal(ipc_msg, self.msg_short)
        # Send message to IPC output & receive from RMQ output
        self.instance.oipc.ipc_send_nolimit(ipc_msg)
        method_frame, header_frame, rmq_msg = self.temp_basic_get()
        nt.assert_equal(rmq_msg, self.msg_short)
        
