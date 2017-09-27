import pika
from cis_interface.drivers.RMQDriver import RMQDriver
from cis_interface.drivers.RPCDriver import RPCDriver
from cis_interface import backwards


_new_client_msg = backwards.unicode2bytes("PSI_NEW_CLIENT")
_end_client_msg = backwards.unicode2bytes("PSI_END_CLIENT")


class RMQServerDriver(RMQDriver, RPCDriver):
    r"""Class for handling server side RPC type RabbitMQ communication.

    Args:
        name (str): The name of the local IPC message queues that the driver
            should use.
        args (str, optional): The name of the RabbitMQ message queue that the
            driver should connect to. Defaults to name + '_SERVER' if not set.
        \*\*kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    Attributes (in addition to the parent class's):
        clients (set): The unique clients subscribed to this server.
    
    .. todo Handle possibility of message larger than AMQP server memory.

    """

    def __init__(self, name, args=None, **kwargs):
        if args is None:
            args = name + '_SERVER'
        super(RMQServerDriver, self).__init__(name, queue=args, **kwargs)
        self.debug()
        self.clients = set([])

    @property
    def n_clients(self):
        r"""int: The number of clients that are submitting requests to the
        server."""
        return len(self.clients)

    def on_queue_declareok(self, method_frame):
        r"""Actions to perform once the queue is succesfully declared."""
        self.debug('::Declaring the server request queue.')
        self.purge_queue()
        super(RMQServerDriver, self).on_queue_declareok(method_frame)

    def start_communication(self, no_ack=False):
        r"""Start consuming messages from the queue."""
        self.debug('::start_consuming')
        self.channel.basic_qos(prefetch_count=1)
        self.channel.add_on_cancel_callback(self.on_cancelok)
        self.consumer_tag = self.channel.basic_consume(self.on_message,
                                                       queue=self.queue)

    def on_message(self, ch, method, props, body):
        r"""Actions to perform when a message is received."""
        if not self.is_valid:  # pragma: debug
            return
        if body == _new_client_msg:
            self.debug('::New client (%s)' % props.reply_to)
            self.clients.add(props.reply_to)
        elif body == _end_client_msg:
            self.debug('::Client signed off (%s)' % props.reply_to)
            if props.reply_to in self.clients:
                self.clients.remove(props.reply_to)
            else:  # pragma: debug
                self.debug(('::Client signing off (%s) is not one of ' +
                            'the recorded clients for this server (%s).'),
                           props.reply_to, str(self.clients))
            if self.n_clients == 0:
                self.debug('::All clients have signed off. Stopping.')
                # Moved to runner level control to prevent mis-communication
                # self.stop()
        elif props.reply_to is None:
            self.debug('::Message received without reply queue.')
            with self.lock:
                if not self.channel_stable:  # pragma: debug
                    return
                # TODO: Requeue?
                self.channel.basic_reject(delivery_tag=method.delivery_tag,
                                          requeue=False)
        else:
            self.clients.add(props.reply_to)
            self.debug('::Message received')
            self.iipc.ipc_send_nolimit(body)
            response = self.oipc.recv_wait_nolimit()
            with self.lock:
                if not self.channel_stable:  # pragma: debug
                    return
                ch.basic_publish(exchange=self.exchange,
                                 routing_key=props.reply_to,
                                 properties=pika.BasicProperties(
                                     correlation_id=props.correlation_id),
                                 body=response)
        with self.lock:
            if not self.channel_stable:  # pragma: debug
                return
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def stop_communication(self):
        r"""Stop sending/receiving messages."""
        super(RMQServerDriver, self).stop_communication(cancel_consumer=True)
