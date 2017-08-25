import pika
import nose.tools as nt
import test_RMQDriver as parent1
import test_RPCDriver as parent2
from RMQClientDriver import _new_client_msg, _end_client_msg


class TestRMQClientDriver(parent1.TestRMQDriver, parent2.TestRPCDriver):
    r"""Test class for RMQClientDriver class."""

    def __init__(self):
        super(TestRMQClientDriver, self).__init__()
        self.driver = 'RMQClientDriver'
        self.args = 'TestServer'
        self.attr_list += ['request_queue', 'response', 'corr_id',
                           '_deliveries', '_acked', '_nacked',
                           '_message_number']
        self._temp_queue = self.args

    def setup(self):
        r"""Recover new client message on start-up."""
        super(TestRMQClientDriver, self).setup()
        nt.assert_equal(self.instance.request_queue, self.temp_queue)
        # New client message
        method_frame, props, rmq_msg = self.temp_basic_get()
        print 'received setup', rmq_msg
        self.channel.basic_ack(delivery_tag = method_frame.delivery_tag)
        nt.assert_equal(rmq_msg, _new_client_msg)
        
    def teardown(self):
        r"""Recover end client message on teardown."""
    #     self.instance.stop()
    #     # End client message
    #     method_frame, props, rmq_msg = self.temp_basic_get()
    #     print 'received teardown', rmq_msg
    #     self.channel.basic_ack(delivery_tag = method_frame.delivery_tag)
    #     nt.assert_equal(rmq_msg, _end_client_msg)
    # #     self.temp_basic_pub(rmq_msg)
        # Purge queues
        self.channel.queue_purge(queue=self.temp_queue)
        self.instance.purge_queue()
    #     # Parent teardown
    #     # raise Exception
    #     print 'parent teardown'
        super(TestRMQClientDriver, self).teardown()
    #     print 'teardown done'

    def test_msg(self):
        r"""Test routing of a message through the IPC & RMQ queues."""
        # Send message to IPC output & receive from RMQ output
        self.instance.oipc.ipc_send_nolimit(self.msg_short)
        method_frame, props, rmq_msg = self.temp_basic_get()
        nt.assert_equal(rmq_msg, self.msg_short)
        self.temp_basic_pub(rmq_msg)
        # Send message to RMQ input & receive from IPC input
        self.instance.channel.basic_publish(
            exchange=self.instance.exchange,
            routing_key=self.instance.queue,
            properties=pika.BasicProperties(
                correlation_id=self.instance.corr_id),
            body=rmq_msg)
        self.channel.basic_ack(delivery_tag = method_frame.delivery_tag)
        ipc_msg = self.instance.iipc.recv_wait_nolimit()
        nt.assert_equal(ipc_msg, self.msg_short)
        
