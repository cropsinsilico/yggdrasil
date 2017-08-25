import os
import pika
import uuid
from RMQDriver import RMQDriver
from RPCDriver import RPCDriver
from RMQServerDriver import _new_client_msg, _end_client_msg


class RMQClientDriver(RMQDriver, RPCDriver):
    r"""Class for handling client side RPC type RabbitMQ communication.

    Args:
        name (str): The name of the local IPC message queues that the driver
            should use.
        args (str, optional): The name of the server RabbitMQ message queue
            that requests should be sent to. Defaults to name + '_SERVER' if
            not set.
        \*\*kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    Attributes (in addition to the parent class's):
        request_queue (str): The name of RabbitMQ message queue that requests
            will be sent to. (See args above).
        response (str): Response to the most recent request.
        corr_id (str): Correlation id for the most recent request.

    """

    def __init__(self, name, args=None, **kwargs):
        super(RMQClientDriver, self).__init__(name, queue="", **kwargs)
        self.debug()
        if args is None:
            args = name + '_SERVER'
        self.request_queue = args
        self.response = None
        self.corr_id = None
        self._deliveries = []
        self._acked = 0
        self._nacked = 0
        self._message_number = 0

    def reconnect(self):
        r"""Reconnect the connection, resetting counts."""
        self._deliveries = []
        self._acked = 0
        self._nacked = 0
        self._message_number = 0

    def on_queue_declareok(self, method_frame):
        r"""Actions to perform once the queue is succesfully declared."""
        self.debug('::Declaring the server request queue.')
        self.channel.queue_declare(
            self.on_request_queue_declareok,
            queue=self.request_queue, auto_delete=True)
        super(RMQClientDriver, self).on_queue_declareok(method_frame)

    def on_request_queue_declareok(self, method_frame):
        r"""Actions to perform once the request queue is succesfully declared.
        This is needed to ensure that the server queue exists when publishing
        begins."""
        self.debug('::Declared the server request queue.')
        self.request_queue = method_frame.method.queue

    def start_communication(self, no_ack=False):
        r"""Start publishing messages to the queue."""
        self.debug('::start_communication')
        self.channel.add_on_cancel_callback(self.on_consumer_cancelled)
        self.consumer_tag = self.channel.basic_consume(self.on_response,
                                                       no_ack=True,
                                                       queue=self.queue)
        self.call(_new_client_msg)
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
    #     print self._deliveries, method_frame.method.delivery_tag
    #     self._deliveries.remove(method_frame.method.delivery_tag)
    #     self.debug('Published %i messages, %i have yet to be confirmed, '
    #                '%i were acked and %i were nacked',
    #                self._message_number, len(self._deliveries),
    #                self._acked, self._nacked)

    def schedule_next_message(self):
        r"""Wait for next message."""
        while True:
            if self._closing:
                return
            self.debug('Checking IPC queue.')
            message = self.oipc.ipc_recv_nolimit()
            if message is None:
                self.debug("::IPC queue closed!")
                break
            elif len(message) == 0:
                self.debug('::Checking in IPC queue again in %0.1f seconds',
                           self.sleeptime)
                self.connection.add_timeout(self.sleeptime,
                                            self.schedule_next_message)
                break
            self.debug("::IPC recv got %d byte request",
                       len(message))
            response = self.call(message)
            self.debug("::Sending %d byte response to IPC", len(response))
            self.iipc.ipc_send_nolimit(response)

    def call(self, message, timeout=None, no_response=False):
        r"""Look for message in IPC queue to publish."""
        if self._closing and not no_response:
            return
        print message[:min(len(message), 10)]
        self.debug(".publish_message(): sending %d bytes to AMQP", len(message))
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange=self.exchange,
                                   routing_key=self.request_queue,
                                   properties=pika.BasicProperties(
                                       reply_to = self.queue,
                                       correlation_id = self.corr_id),
                                   body=message)
        self._message_number += 1
        self._deliveries.append(self._message_number)
        print 'published', self._deliveries
        if no_response:
            return None
        time_elapsed = 0.0
        while self.response is None:
            if (timeout is not None) and (time_elapsed >= timeout):
                break
            # self.connection.process_data_events()
            self.sleep()
            time_elapsed += self.sleeptime
        print 'response', self.response
        return self.response

    def on_consumer_cancelled(self, method_frame):
        r"""Actions to perform when consumption is cancelled."""
        self.debug('::Consumer was cancelled remotely, shutting down: %r',
                   method_frame)
        if self.channel:
            self.channel.close()

    def on_response(self, ch, method, props, body):
        r"""Actions to perform when a reponse is received from the server."""
        if self.corr_id == props.correlation_id:
            self.debug("::Received %d byte response", len(body))
            self.response = body
        # TODO: put message back in queue if its wrong?

    def stop_communication(self):
        r"""Stop consuming messages from the queue."""
        self._closing = True
        if self.channel:
            self.debug("::Cancelling consumption.")
            # print 'calling ', _end_client_msg
            # self.call(_end_client_msg, no_response=True)
            # print 'call done'
            self.channel.close()
            print 'channel closed'
            # self.channel.basic_publish(exchange=self.exchange,
            #                            routing_key=self.request_queue,
            #                            body=_end_client_msg)
