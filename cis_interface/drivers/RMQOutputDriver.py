"""Module for sending output to a RabbitMQ server."""
from cis_interface.drivers.RMQDriver import RMQDriver
from cis_interface.drivers.IODriver import IODriver


class RMQOutputDriver(RMQDriver, IODriver):
    r"""Driver for sending output to a RabbitMQ server.

    Args:
        name (str): The name of the local message queue that the driver should
            connect to.
        args (str): The name of the RabbitMQ message queue that the driver
            connect to.
        \*\*kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    Attributes (in addition to parent class's):
        -

    """
    
    def __init__(self, name, args, **kwargs):
        super(RMQOutputDriver, self).__init__(
            name, suffix="_OUT", queue=args, **kwargs)
        self.debug()

    def start_communication(self):
        r"""Start publishing messages from the local queue."""
        self.debug('::start_communication')
        self.publish_message()
    
    def publish_message(self):
        r"""Continue receiving messages from the local queue and passing them
        to the RabbitMQ server until the queue is closed."""
        if not self.channel_stable:  # pragma: debug
            return
        while self.is_valid:
            self.debug("::publish_message(): IPC recv")
            data = self.ipc_recv()
            if data is None:  # pragma: debug
                self.debug("::publish_message(): queue closed!")
                # print 'terminate'
                # self.terminate()
                break
            elif len(data) == 0:
                self.debug("::publish_message(): no data, reschedule")
                with self.lock:
                    if not self.channel_stable:  # pragma: debug
                        return
                    self.connection.add_timeout(self.sleeptime,
                                                self.publish_message)
                break
            self.debug("::publish_message(): IPC recv got %d bytes", len(data))
            self.debug("::publish_message(): send %d bytes to AMQP", len(data))
            with self.lock:
                if not self.channel_stable:  # pragma: debug
                    return
                self.channel.basic_publish(
                    exchange=self.exchange, routing_key=self.queue,
                    body=data, mandatory=True)
            self.debug("::publish_message(): sent to AMQP")
        self.debug("::publish_message returns")

    def stop_communication(self, **kwargs):
        r"""Stop sending/receiving messages. Only RMQInputDriver should
        explicitly delete the queue."""
        super(RMQOutputDriver, self).stop_communication(
            remove_queue=False, **kwargs)
