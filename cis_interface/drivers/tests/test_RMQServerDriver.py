import pika
import time
import nose.tools as nt
import test_RMQDriver as parent1
from test_IODriver import IOInfo
from cis_interface.drivers.RMQServerDriver import (
    _new_client_msg, _end_client_msg)


class TestRMQServerParam(parent1.TestRMQParam, IOInfo):
    r"""Test parameters for RMQServerDriver class.

    Attributes (in addition to parent class's):
        -

    """

    def __init__(self, *args, **kwargs):
        super(TestRMQServerParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQServerDriver'
        self.args = None
        self.attr_list += ['clients']
        

class TestRMQServerDriverNoStart(TestRMQServerParam,
                                 parent1.TestRMQDriverNoStart):
    r"""Test class for RMQServerDriver class without start.

    Attributes (in addition to parent class's):
        -

    """
    pass


class TestRMQServerDriver(TestRMQServerParam, parent1.TestRMQDriver):
    r"""Test class for RMQServerDriver class.

    Attributes (in addition to parent class's):
        -

    """

    def setup(self):
        r"""Create a driver instance and start the driver."""
        super(TestRMQServerDriver, self).setup()
        self.create_in_rmq()

    def teardown(self):
        r"""Remove the instance, stoppping it."""
        self.destroy_in_rmq()
        super(TestRMQServerDriver, self).teardown()

    def create_in_rmq(self):
        r"""Create a blocking connection, channel, and queue for testing."""
        self.connection = pika.BlockingConnection(
            self.instance.connection_parameters)
        self.channel = self.connection.channel()
        out = self.channel.queue_declare(auto_delete=True)
        self.temp_queue = out.method.queue
        self.channel.queue_bind(
            queue=self.temp_queue,
            exchange=self.instance.exchange,
            routing_key=self.temp_queue)

    def destroy_in_rmq(self):
        r"""Remove blocking connection, channel, and queue."""
        self.channel.queue_unbind(self.temp_queue,
                                  exchange=self.instance.exchange)
        self.channel.queue_delete(self.temp_queue)
        self.channel.close()
        self.connection.close()

    def temp_basic_get(self):
        r"""Do basic_get from the temporary queue."""
        out = self.channel.basic_get(queue=self.temp_queue)
        tries = 5
        while out[0] is None and tries > 0:
            self.connection.sleep(self.instance.sleeptime)
            out = self.channel.basic_get(queue=self.temp_queue)
            tries -= 1
        if out[0] is None:  # pragma: debug
            raise Exception("Msg receive timed out.")
        return out

    def test_client_count(self):
        r"""Test to ensure client count is correct."""
        nt.assert_equal(self.instance.n_clients, 0)
        # Send new client message
        with self.instance.lock:
            self.instance.channel.basic_publish(
                exchange=self.instance.exchange,
                routing_key=self.instance.queue,
                properties=pika.BasicProperties(reply_to=self.temp_queue),
                body=_new_client_msg)
        time.sleep(0.1)
        nt.assert_equal(self.instance.n_clients, 1)
        # Send end client message
        with self.instance.lock:
            self.instance.channel.basic_publish(
                exchange=self.instance.exchange,
                routing_key=self.instance.queue,
                properties=pika.BasicProperties(reply_to=self.temp_queue),
                body=_end_client_msg)
        time.sleep(0.1)
        nt.assert_equal(self.instance.n_clients, 0)

    def test_msg(self):
        r"""Test routing of a message through the IPC & RMQ queues."""
        # Send message to RMQ input & receive from IPC input
        with self.instance.lock:
            self.instance.channel.basic_publish(
                exchange=self.instance.exchange,
                routing_key=self.instance.queue,
                properties=pika.BasicProperties(reply_to=self.temp_queue),
                body=self.msg_short)
        ipc_msg = self.instance.iipc.recv_wait_nolimit()
        nt.assert_equal(ipc_msg, self.msg_short)
        # Send message to IPC output & receive from RMQ output
        self.instance.oipc.ipc_send_nolimit(ipc_msg)
        method_frame, header_frame, rmq_msg = self.temp_basic_get()
        nt.assert_equal(rmq_msg, self.msg_short)
