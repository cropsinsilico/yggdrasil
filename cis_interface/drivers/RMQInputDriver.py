"""Module for receiving input from a RabbitMQ server."""
from cis_interface.drivers.RMQDriver import RMQDriver
from cis_interface.drivers.IODriver import IODriver


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

    def start_communication(self):
        r"""Begin consuming messages and add the callback for cancelling
        consumption."""
        self.debug('::start_communication')
        # one at a time, don't stuff the Qs
        if self.channel_stable:
            self.channel.basic_qos(prefetch_count=1)
            self._consumer_tag = self.channel.basic_consume(
                self.on_message, queue=self.queue)

    def on_message(self, ch, method, props, body):
        r"""Action to perform when a message is received. Send it to the
        local queue and acknowledge the message."""
        self.debug('::on_message: received message # %s from %s',
                   method.delivery_tag, props.app_id)
        if not self.channel_stable:  # pragma: debug
            return
        self.ipc_send(body)
        with self.lock:
            if not self.channel_stable:  # pragma: debug
                return
            ch.basic_ack(delivery_tag=method.delivery_tag)
