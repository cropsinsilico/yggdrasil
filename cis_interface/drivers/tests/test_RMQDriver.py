import os
import pika
import nose.tools as nt
import test_Driver as parent


class TestRMQParam(parent.TestParam):
    r"""Test parameters for RMQDriver class.

    Attributes (in addition to parent class's):
        -

    """

    def __init__(self):
        super(TestRMQParam, self).__init__()
        self.driver = 'RMQDriver'
        self.args = None
        self.attr_list += ['user', 'server', 'passwd', 'exchange',
                           'connection', 'queue', 'channel',
                           'routing_key', 'consumer_tag',
                           '_opening', '_closing', 'times_connected']
        self._temp_queue = ''
        self._connection = None
        self._channel = None
        self.inst_kwargs['user'] = os.environ.get('PSI_MSG_USER', None)

        
class TestRMQDriverNoStart(TestRMQParam, parent.TestDriverNoStart):
    r"""Test class for RMQDriver class without start.

    Attributes (in addition to parent class's):
        -

    """
    pass


class TestRMQDriver(TestRMQParam, parent.TestDriver):
    r"""Test class for RMQDriver class.

    Attributes (in addition to parent class's):
        -

    """

    def teardown(self):
        r"""Make sure the queue is empty before closing the driver."""
        self.instance.purge_queue()
        super(TestRMQDriver, self).teardown()

    def declare_temp_queue(self):
        r"""Create a blocking connection, channel, and queue for testing."""
        self._connection = pika.BlockingConnection(
            self.instance.connection_parameters)
        self._channel = self._connection.channel()
        out = self._channel.queue_declare(
            queue=self._temp_queue,
            auto_delete=True)
        self._temp_queue = out.method.queue
        self._channel.queue_bind(
            queue=self._temp_queue,
            exchange=self.instance.exchange,
            routing_key=self._temp_queue)

    @property
    def temp_queue(self):
        r"""Temporary queue for responses etc."""
        if not self._temp_queue:
            self.declare_temp_queue()
        return self._temp_queue

    @property
    def connection(self):
        r"""Temporary connection."""
        if self._connection is None:  # pragma: debug
            self.declare_temp_queue()
        return self._connection
        
    @property
    def channel(self):
        r"""Temporary channel."""
        if self._channel is None:
            self.declare_temp_queue()
        return self._channel
        
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

    def temp_basic_pub(self, msg, routing_key=None, properties=None):
        r"""Do basic_publish tot he temporary queue."""
        if routing_key is None:  # pragma: debug
            routing_key = self.temp_queue
        self.channel.basic_publish(exchange=self.instance.exchange,
                                   routing_key=routing_key,
                                   properties=properties,
                                   body=msg)

    def test_purge(self):
        r"""Test purge of queue."""
        self.instance.purge_queue()

    def assert_after_terminate(self):
        r"""Make sure the connection is closed."""
        nt.assert_equal(self.instance.connection, None)
        nt.assert_equal(self.instance.channel, None)
        assert(not self.instance._opening)
        assert(not self.instance._closing)
        super(TestRMQDriver, self).assert_after_terminate()

    # def test_reconnect(self):
    #     r"""Close the connection to simulation failure and force reconnect."""
    #     if self.driver == 'RMQDriver':
    #         with self.instance.lock:
    #             self.instance.connection.close(reply_code=100,
    #                                            reply_text="Test shutdown")
    #         self.instance.sleep()
        # import time
        # time.sleep(10)
        # print(self.instance.times_connected, 'times', self.instance._opening,
        #       self.instance._closing)
        # self.instance.sleep()
        # self.instance.sleep()
