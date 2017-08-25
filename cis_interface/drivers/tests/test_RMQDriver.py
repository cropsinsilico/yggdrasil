import pika
import test_Driver as parent


class TestRMQDriver(parent.TestDriver):
    r"""Test class for RMQDriver class."""

    def __init__(self):
        super(TestRMQDriver, self).__init__()
        self.driver = 'RMQDriver'
        self.args = None
        self.attr_list += ['user', 'server', 'passwd', 'exchange',
                           'connection', 'queue', 'channel',
                           'routing_key', 'consumer_tag',
                           '_opening', '_closing']
        self._temp_queue = ''
        self._connection = None
        self._channel = None

    def declare_temp_queue(self):
        self._connection = pika.BlockingConnection(
            self.instance.connection_parameters)
        self._channel = self._connection.channel()
        out = self._channel.queue_declare(
            queue=self._temp_queue,
            #exclusive=True,
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
        if self._connection is None:
            self.declare_temp_queue()
        return self._connection
        
    @property
    def channel(self):
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
        if out[0] is None:
            raise Exception("Msg receive timed out.")
        return out

    def temp_basic_pub(self, msg, properties=None):
        r"""Do basic_publish tot he temporary queue."""
        self.channel.basic_publish(exchange=self.instance.exchange,
                                   routing_key=self.temp_queue,
                                   properties=properties,
                                   body=msg)
