"""Module for receiving input from a RabbitMQ server."""
import requests
from pprint import pformat
from RMQDriver import RMQDriver
from IODriver import IODriver


class RMQInputDriver(RMQDriver, IODriver):
    r"""Driver for receiving input from a RabbitMQ server.

    Args:
        name (str): The name of the local message queue that the driver should
            connect to.
        args (str): The name of the RabbitMQ message queue that the driver
            should connect to.
        \*\*kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    Attributes (in addition to parent class's):
        -

    """

    def __init__(self, name, args, **kwargs):
        super(RMQInputDriver, self).__init__(
            name, suffix="_IN", queue=args, **kwargs)
        self.debug()

    def printStatus(self):
        r"""Print the driver status."""
        self.debug('::printStatus')
        super(RMQInputDriver, self).printStatus()
        url = 'http://%s:%s/api/%s/%s/%s' % (
            self.server, 15672, 'queues', '%2f', self.queue)
        res = requests.get(url, auth=(self.user, self.passwd))
        jdata = res.json()
        qdata = jdata.get('message_stats', '')
        self.error(": server info: %s", pformat(qdata))

    def start_communication(self):
        r"""Begin consuming messages and add the callback for cancelling
        consumption."""
        self.debug('::start_communication')
        # one at a time, don't stuff the Qs
        self.channel.basic_qos(prefetch_count=1)
        self._consumer_tag = self.channel.basic_consume(
            self.on_message, queue=self.queue)

    def on_message(self, ch, method, props, body):
        r"""Action to perform when a message is received. Send it to the
        local queue and acknowledge the message."""
        self.debug('::on_message: received message # %s from %s',
                   method.delivery_tag, props.app_id)
        with self.lock:
            if self._closing:
                return
        self.ipc_send(body)
        with self.lock:
            if self._closing:
                return
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def stop_communication(self, **kwargs):
        r"""Stop sending/receiving messages. Only RMQInputDriver should
        explicitly delete the queue."""
        with self.lock:
            self._closing = True
            if self.channel:
                self.channel.queue_unbind(queue=self.queue,
                                          exchange=self.exchange)
                self.channel.queue_delete(queue=self.queue)
                self.channel.close()

    # def on_model_exit(self):
    #     r"""Delete the driver. Unbinding and deleting the queue and closing
    #     the connection."""
    #     self.debug('::delete')
    #     try:
    #         self.channel.queue_unbind(exchange=self.exchange, queue=self.queue)
    #         # self.channel.queue_delete(queue=self.queue, if_unused=True)
    #         # self.connection.close()
    #     except:
    #         self.debug("::delete(): exception (IGNORED)")
    #     self.debug('::delete done')
