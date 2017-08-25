import os
import pika
from RMQDriver import RMQDriver
from RPCDriver import RPCDriver

_new_client_msg = "PSI_NEW_CLIENT"
_end_client_msg = "PSI_END_CLIENT"


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
        n_clients (int): The number of clients that are submitting requests to
            the server.
    
    """

    def __init__(self, name, args=None, **kwargs):
        if args is None:
            args = name + '_SERVER'
        super(RMQServerDriver, self).__init__(name, queue=args, **kwargs)
        self.debug()
        self.n_clients = 0

    def start_communication(self, no_ack=False):
        r"""Start consuming messages from the queue."""
        self.debug('::start_consuming')
        self.channel.add_on_cancel_callback(self.on_consumer_cancelled)
        self.channel.basic_qos(prefetch_count=1)
        self.consumer_tag = self.channel.basic_consume(self.on_message,
                                                       queue=self.queue)

    def on_consumer_cancelled(self, method_frame):
        r"""Actions to perform when consumption is cancelled."""
        self.debug('::Consumer was cancelled remotely, shutting down: %r',
                   method_frame)
        if self.channel:
            self.channel.close()

    def on_message(self, ch, method, props, body):
        r"""Actions to perform when a message is received."""
        # TODO: handle possibility of message larger than AMQP server memory
        if body == _new_client_msg:
            self.debug('::New client')
            self.n_clients += 1
        elif body == _end_client_msg:
            self.debug('::Client signed off')
            self.n_clients -= 1
        else:
            self.debug('::Message received')
            self.iipc.ipc_send_nolimit(body)
            response = self.oipc.recv_wait_nolimit()
            ch.basic_publish(exchange=self.exchange,
                             routing_key=props.reply_to,
                             properties=pika.BasicProperties(
                                 correlation_id = props.correlation_id),
                             body=str(response))
        ch.basic_ack(delivery_tag = method.delivery_tag)

    def stop_communication(self):
        r"""Stop consuming messages from the queue."""
        self._closing = True
        if self.channel:
            self.debug("::Cancelling consumption.")
            self.channel.basic_cancel(callback=self.on_cancelok,
                                      consumer_tag=self.consumer_tag)
            
    def on_cancelok(self, unused_frame):
        r"""Actions to perform after succesfully cancelling consumption."""
        self.channel.close()
