import pika
import uuid
from cis_interface.drivers.RMQDriver import RMQDriver
from cis_interface.drivers.RPCDriver import RPCDriver
from cis_interface.drivers.RMQServerDriver import (
    _new_client_msg, _end_client_msg)


class RMQClientDriver(RMQDriver, RPCDriver):
    r"""Class for handling client side RPC type RabbitMQ communication.

    Args:
        name (str): The name of the local IPC message queues that the driver
            should use.
        args (str, optional): The name of the server RabbitMQ message queue
            that requests should be sent to. Defaults to name + '_SERVER' if
            not set.
        **kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    Attributes:
        request_queue (str): The name of RabbitMQ message queue that requests
            will be sent to. (See args above).
        response (str): Response to the most recent request.
        corr_id (str): Correlation id for the most recent request.

    """

    def __init__(self, name, args=None, **kwargs):
        if args is None:
            args = name + '_SERVER'
        super(RMQClientDriver, self).__init__(name, queue="", **kwargs)
        self.debug()
        self.request_queue = args
        self.response = None
        self.corr_id = None
        self._deliveries = []
        self._acked = 0
        self._nacked = 0
        self._message_number = 0

    # def reconnect(self):
    #     r"""Reconnect the connection, resetting counts."""
    #     self._deliveries = []
    #     self._acked = 0
    #     self._nacked = 0
    #     self._message_number = 0
    #     super(RMQClientDriver, self).reconnect()

    # If we force the RMQServerDriver to start the request queue, it can
    # purge the queue before starting to ensure a new run
    # def on_queue_declareok(self, method_frame):
    #     r"""Actions to perform once the queue is succesfully declared."""
    #     self.debug('::Declaring the server request queue.')
    #     self.channel.queue_declare(
    #         self.on_request_queue_declareok,
    #         queue=self.request_queue, auto_delete=True)
    #     super(RMQClientDriver, self).on_queue_declareok(method_frame)

    # def on_request_queue_declareok(self, method_frame):
    #     r"""Actions to perform once the request queue is succesfully declared.
    #     This is needed to ensure that the server queue exists when publishing
    #     begins."""
    #     self.debug('::Declared the server request queue.')
    #     self.request_queue = method_frame.method.queue

    def start_communication(self, no_ack=False):
        r"""Start publishing messages to the queue."""
        self.debug('::start_communication')
        self.channel.basic_qos(prefetch_count=1)
        if self.times_connected == 1:  # Only do this once
            self.publish_to_server(_new_client_msg)
        self.channel.add_on_cancel_callback(self.on_cancelok)
        self.consumer_tag = self.channel.basic_consume(self.on_response,
                                                       # no_ack=True,
                                                       queue=self.queue)
        self.start_publishing()

    def start_publishing(self):
        r"""Begin moving messages from IPC queue to RMQ queue."""
        self.debug('::start_publishing')
        # self.enable_delivery_confirmations()
        self.schedule_next_message()

    # def enable_delivery_confirmations(self):
    #     r"""Enable confirmation of delivery."""
    #     self.debug('::Enabling delivery confirmations.')
    #     self.channel.confirm_delivery(self.on_delivery_confirmation)

    # def on_delivery_confirmation(self, method_frame):
    #     r"""Actions to perform when a delivery confirmation is received."""
    #     confirmation_type = method_frame.method.NAME.split('.')[1].lower()
    #     self.debug('Received %s for delivery tag: %i',
    #                confirmation_type,
    #                method_frame.method.delivery_tag)
    #     if confirmation_type == 'ack':
    #         self._acked += 1
    #     elif confirmation_type == 'nack':
    #         self._nacked += 1
    #     print(self._deliveries, method_frame.method.delivery_tag)
    #     self._deliveries.remove(method_frame.method.delivery_tag)
    #     self.debug('Published %i messages, %i have yet to be confirmed, '
    #                '%i were acked and %i were nacked',
    #                self._message_number, len(self._deliveries),
    #                self._acked, self._nacked)

    def schedule_next_message(self):
        r"""Wait for next message."""
        if not self.channel_stable:  # pragma: debug
            return
        self.debug('Checking IPC queue.')
        message = self.oipc.ipc_recv_nolimit()
        if message is None:  # pragma: debug
            self.debug("::IPC queue closed!")
            return
        elif len(message) == 0:
            self.debug('::Checking in IPC queue again in %5.2f seconds',
                       self.sleeptime)
            with self.lock:
                if not self.channel_stable:  # pragma: debug
                    return
                self.connection.add_timeout(self.sleeptime,
                                            self.schedule_next_message)
        else:
            self.debug("::IPC recv got %d byte request", len(message))
            self.publish_to_server(message)
            self.schedule_next_response()

    def schedule_next_response(self):
        r"""Wait for next response."""
        if not self.channel_stable:  # pragma: debug
            return
        if self.response is None:
            self.debug('::Checking RMQ response queue again in %5.2f seconds',
                       self.sleeptime)
            with self.lock:
                if not self.channel_stable:  # pragma: debug
                    return
                self.connection.add_timeout(self.sleeptime,
                                            self.schedule_next_response)
        else:
            self.debug("::Sending %d byte response to IPC", len(self.response))
            self.iipc.ipc_send_nolimit(self.response)
            self.schedule_next_message()

    def publish_to_server(self, message, properties=None):
        r"""Publish a message to the server queue."""
        with self.lock:
            if not self.channel_stable:  # pragma: debug
                return
            self.debug(".publish_message(): sending %d bytes to AMQP", len(message))
            self.response = None
            self.response_time = 0.0
            self.corr_id = str(uuid.uuid4())
            self.channel.basic_publish(exchange=self.exchange,
                                       routing_key=self.request_queue,
                                       properties=pika.BasicProperties(
                                           reply_to=self.queue,
                                           correlation_id=self.corr_id),
                                       body=message)
            self._message_number += 1
            self._deliveries.append(self._message_number)

    def on_response(self, ch, method, props, body):
        r"""Actions to perform when a reponse is received from the server."""
        with self.lock:
            if self.corr_id == props.correlation_id:
                self.debug("::Received %d byte response", len(body))
                self.response = body
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                # TODO: requeue rejected message
                ch.basic_reject(method.delivery_tag, requeue=False)

    def stop_communication(self):
        r"""Stop consuming messages from the queue."""
        with self.lock:
            if self.channel_stable:
                self.debug("::Cancelling consumption.")
                self.publish_to_server(_end_client_msg)
        super(RMQClientDriver, self).stop_communication(cancel_consumer=True)
