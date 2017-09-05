import os
import pika
import nose.tools as nt
import test_RMQDriver as parent1
from test_IODriver import IOInfo
from cis_interface.drivers.RMQClientDriver import (
    _new_client_msg, _end_client_msg)
from cis_interface import runner
from cis_interface.examples import yamls as ex_yamls


def test_yaml():
    r"""Test Server/Client setup using runner."""
    os.environ['FIB_ITERATIONS'] = '3'
    os.environ['FIB_SERVER_SLEEP_SECONDS'] = '1'
    cr = runner.get_runner(ex_yamls['rpcfib_python'])
    cr.run()


class TestRMQClientParam(parent1.TestRMQParam, IOInfo):
    r"""Test parameters for RMQClientDriver class.

    Attributes (in addition to parent class's):
        -

    """

    def __init__(self):
        super(TestRMQClientParam, self).__init__()
        self.driver = 'RMQClientDriver'
        self.args = None
        self.attr_list += ['request_queue', 'response', 'corr_id',
                           '_deliveries', '_acked', '_nacked',
                           '_message_number']
        self._temp_queue = 'TestRMQClientDriver_SERVER'
        if getattr(self, 'channel', None):
            self.channel.queue_purge(queue=self.temp_queue)
            

class TestRMQClientDriverNoStart(TestRMQClientParam,
                                 parent1.TestRMQDriverNoStart):
    r"""Test class for RMQClientDriver class without start.

    Attributes (in addition to parent class's):
        -

    """
    pass


class TestRMQClientDriver(TestRMQClientParam, parent1.TestRMQDriver):
    r"""Test class for RMQClientDriver class.

    Attributes (in addition to parent class's):
        -

    """

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
        
