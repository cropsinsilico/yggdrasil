import pika
import nose.tools as nt
import test_RMQDriver as parent1
from test_IODriver import IOInfo
from cis_interface.drivers.RMQClientDriver import (
    _new_client_msg, _end_client_msg)


class TestRMQClientDriver(parent1.TestRMQDriver, IOInfo):
    r"""Test class for RMQClientDriver class."""

    def __init__(self):
        super(TestRMQClientDriver, self).__init__()
        self.driver = 'RMQClientDriver'
        self.args = None
        self.attr_list += ['request_queue', 'response', 'corr_id',
                           '_deliveries', '_acked', '_nacked',
                           '_message_number']
        self._temp_queue = 'TestRMQClientDriver_SERVER'
        if self.channel:
            self.channel.queue_purge(queue=self.temp_queue)

    def setup(self):
        r"""Recover new client message on start-up."""
        super(TestRMQClientDriver, self).setup()
        nt.assert_equal(self.instance.request_queue, self.temp_queue)
        # New client message
        method_frame, props, rmq_msg = self.temp_basic_get()
        self.channel.basic_ack(delivery_tag = method_frame.delivery_tag)
        # print('received setup', rmq_msg)        
        nt.assert_equal(rmq_msg, _new_client_msg)
        
    def teardown(self):
        r"""Recover end client message on teardown."""
        self.instance.stop()
        # End client message
        method_frame, props, rmq_msg = self.temp_basic_get()
        self.channel.basic_ack(delivery_tag = method_frame.delivery_tag)
        # print('received teardown', rmq_msg)
        nt.assert_equal(rmq_msg, _end_client_msg)
        # Parent teardown
        super(TestRMQClientDriver, self).teardown()

    def test_msg(self):
        r"""Test routing of a message through the IPC & RMQ queues."""
        # Send message to IPC output & receive from RMQ output
        self.instance.oipc.ipc_send_nolimit(self.msg_short)
        method_frame, props, rmq_msg = self.temp_basic_get()
        nt.assert_equal(rmq_msg, self.msg_short)
        # Send message to RMQ input & receive from IPC input
        self.temp_basic_pub(
            rmq_msg, routing_key=props.reply_to,
            properties=pika.BasicProperties(
                correlation_id=props.correlation_id))
        # self.channel.basic_ack(delivery_tag = method_frame.delivery_tag)
        ipc_msg = self.instance.iipc.recv_wait_nolimit()
        nt.assert_equal(ipc_msg, self.msg_short)
        
