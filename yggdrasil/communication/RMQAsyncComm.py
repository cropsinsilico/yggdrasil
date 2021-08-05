import functools
from yggdrasil import tools, multitasking
from yggdrasil.communication import RMQComm, NoMessages
from yggdrasil.communication.RMQComm import pika


class RMQAsyncComm(RMQComm.RMQComm):
    r"""Class for handling asynchronous RabbitMQ communications. It is not
    recommended to use this class as it can leave hanging threads if not
    closed propertly. The normal RMQComm will cover most use cases.

    Args:
        name (str): The environment variable where the comm address is stored.
        dont_open (bool, optional): If True, the connection will not be opened.
            Defaults to False.
        **kwargs: Additional keyword arguments are passed to CommBase.

    Attributes:
        times_connected (int): Number of times that this connections has been
            established.
        rmq_thread (multitasking.YggTask): Thread used to run IO loop.

    """
    
    _commtype = 'rmq_async'
    _schema_subtype_description = ('Asynchronous RabbitMQ connection.')
    _disconnect_attr = (RMQComm.RMQComm._disconnect_attr
                        + ['_rmq_thread', '_consuming', '_reconnecting'])

    def _init_before_open(self, **kwargs):
        r"""Initialize null variables and RMQ async thread."""
        self.times_connected = 0
        self.rmq_thread_count = 0
        self.rmq_thread = self.new_run_thread()
        self._consuming = multitasking.ProcessEvent()
        self._reconnecting = multitasking.ProcessEvent()
        self._reconnect_delay = 0
        self._prefetch_count = 2
        self._buffered_messages = []
        self._acked = 0
        self._nacked = 0
        self._message_number = 0
        super(RMQAsyncComm, self)._init_before_open(**kwargs)
        self._opening.stopped.add_callback(self._reconnecting.stop)

    @property
    def rmq_lock(self):
        r"""Lock associated with RMQ ioloop thread."""
        return self.rmq_thread.lock

    def new_run_thread(self, name=None):
        r"""Get a new thread for running."""
        if name is None:
            name = self.name
        self.rmq_thread_count += 1
        return multitasking.YggTask(
            name=name + '.RMQThread%d' % self.rmq_thread_count,
            target=self.run_thread)

    def reset_for_reconnection(self):
        r"""Reset variables in preparation for reconnection."""
        self.connection = None
        self.channel = None
        self._acked = 0
        self._nacked = 0
        self._message_number = 0
        self._consuming.started.clear()
        self._consuming.stopped.clear()
        self._closing.started.clear()
        self._closing.stopped.clear()
        self._consumer_tag = None
        if self.direction == 'send':
            self._buffered_messages = []

    def run_thread(self):
        r"""Connect to the connection and begin the IO loop."""
        while not self._closing.has_started():
            try:
                self.debug('')
                self.connect()
                self.connection.ioloop.start()
                self.debug("returning")
            except BaseException as e:
                self.error("Error in RMQ thread %s: %s", type(e), e)
                self.stop()
                break
            if self._reconnecting.is_running():
                self.stop()
                if self._consuming.has_started():
                    self._reconnect_delay = 0
                else:
                    self._reconnect_delay += 1
                self._reconnect_delay = min(self._reconnect_delay, 30)
                self.info('Reconnecting after %d seconds',
                          self._reconnect_delay)
                self.sleep(self._reconnect_delay)
                self.reset_for_reconnection()

    def start_run_thread(self):
        r"""Start the run thread and wait for it to finish."""
        with self.rmq_lock:
            if self.rmq_thread.was_started:
                return
            self.rmq_thread.start()
        # Wait for connection to be established
        self._opening.stopped.wait(self.timeout)
        # Check that connection was established
        if not self.rmq_thread.is_alive():  # pragma: debug
            self.stop()
            raise Exception("Connection ioloop could not be established.")
        if not self.is_open:  # pragma: debug
            self.stop()
            raise RuntimeError("Connection never finished opening ")

    def bind(self):
        r"""Declare queue to get random new queue."""
        if self._opening.has_started() or self._closing.has_started():
            return
        self._opening.start()
        self.start_run_thread()  # Start ioloop in a new thread
        # Register queue
        if not self.queue:  # pragma: debug
            self.error("Queue was not initialized.")
        self.register_comm(self.address, (self.connection, self.channel))
        super(RMQComm.RMQComm, self).bind()
    
    def _close(self, linger=False):
        r"""Close the connection.

        Args:
            linger (bool, optional): If True, drain messages before closing the
                comm. Defaults to False.

        """
        self.stop()
        self._closing.stopped.wait(self.timeout)
        if not self._closing.has_stopped():
            self.error("Closing has not completed")
        if not self.is_client:
            self.unregister_comm(self.address)
        with self.rmq_lock:
            self.channel = None
            self.connection = None
        super(RMQAsyncComm, self)._close(linger=linger)
        if self.rmq_thread.is_alive():  # pragma: debug
            self.rmq_thread.join(self.timeout)
            if self.rmq_thread.is_alive():
                raise RuntimeError("Thread still running.")

    @property
    def is_open(self):
        r"""bool: True if the connection and channel are open."""
        if self._reconnecting.is_running():
            return True
        return super(RMQAsyncComm, self).is_open

    @property
    def n_msg_recv(self):
        r"""int: Number of messages in the queue."""
        if self.is_open:
            return len(self._buffered_messages)
        return 0

    def _send(self, msg, exchange=None, routing_key=None, **kwargs):
        r"""Send a message.

        Args:
            msg (str, bytes): Message to be sent.
            exchange (str, optional): Exchange that message should be sent
                to. Defaults to self.exchange.
            routing_key (str, optional): Key that exchange should use to route
                the message. Defaults to self.queue.
            **kwargs: Additional keyword arguments are passed to
                :method:`pika.BlockingChannel.basic_publish`.

        Returns:
            bool: Success or failure of send.

        """
        with self.rmq_lock:
            if self.is_closed:  # pragma: debug
                return False
            out = super(RMQAsyncComm, self)._send(msg, exchange=exchange,
                                                  routing_key=routing_key,
                                                  **kwargs)
            if out:
                self._message_number += 1
                self._buffered_messages.append(self._message_number)
                self.debug("Sent message %d", self._message_number)
        return out

    def _recv(self):
        r"""Receive a message.

        Returns:
            tuple (bool, obj): Success or failure of receive and received
                message.

        """
        with self.rmq_lock:
            if len(self._buffered_messages) == 0:
                raise NoMessages("No messages in buffer.")
            return (True, self._buffered_messages.pop(0))

    def close_channel(self):
        r"""Close the channel if it exists."""
        if self.channel:
            self.channel.add_callback(
                self.on_channel_closeok, [pika.spec.Channel.CloseOk])
        super(RMQAsyncComm, self).close_channel()
        
    def close_connection(self):
        r"""Close the connection."""
        self._consuming.stop()
        if self.connection is not None:
            if self.connection.is_closing or self.connection.is_closed:
                self.debug('Connection is closing or already closed')
            else:
                super(RMQAsyncComm, self).close_connection()
        
    # CONNECTION
    def connect(self):
        r"""Establish the connection."""
        self.times_connected += 1
        self.connection = pika.SelectConnection(
            pika.URLParameters(self.url),
            on_open_callback=self.on_connection_open,
            on_open_error_callback=self.on_connection_open_error,
            on_close_callback=self.on_connection_closed)

    def on_connection_open(self, connection):
        r"""Actions that must be taken when the connection is opened.
        Add the close connection callback and open the RabbitMQ channel."""
        self.debug('Connection opened')
        self.open_channel()

    def on_connection_open_error(self, unused_connection, err):  # pragma: debug
        r"""Actions that must be taken when the connection fails to open."""
        self.debug('Connection open failed: %s', err)
        self.reconnect()

    def on_connection_closed(self, connection, reason):
        r"""Actions that must be taken when the connection is closed. Set the
        channel to None. If the connection is meant to be closing, stop the
        IO loop. Otherwise, wait 5 seconds and try to reconnect."""
        with self.rmq_lock:
            self.channel = None
            if self._closing.has_started():
                self.debug('Connection closed')
                self.connection.ioloop.stop()
                self._closing.stop()
            else:
                self.debug('Connection closed, reconnect necessary: %s', reason)
                self.reconnect()

    def stop(self):
        r"""Stop the ioloop."""
        if not self._closing.has_started():
            self._closing.start()
            self.debug('Stopping')
            if self.direction == 'recv':
                if self._consuming.is_running():
                    self.stop_consuming()
                    # Not called here because KeyboardInterrupt is not used
                    # to stop the loop
                    # self.connection.ioloop.start()
                else:
                    self.connection.ioloop.stop()
                self.debug('Stopped')
            else:
                self.close_channel()
                self.close_connection()

    def reconnect(self):
        r"""Try to re-establish a connection and resume a new IO loop."""
        # Stop the old IOLoop, create a new connection and start a new IOLoop
        self.debug('')
        self._reconnecting.started.clear()
        self._reconnecting.stopped.clear()
        self._reconnecting.start()  # stopped by re-opening
        if self.direction == 'recv':
            self._opening.stopped.clear()
            self.stop()
        else:
            self.connection.ioloop.call_later(
                5, self.connection.ioloop.stop)

    # CHANNEL
    def open_channel(self):
        r"""Open a RabbitMQ channel."""
        self.debug('Creating a new channel')
        self.connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        r"""Actions to perform after a channel is opened. Add the channel
        close callback and setup the exchange."""
        self.debug('Channel opened')
        self.channel = channel
        self.add_on_channel_close_callback()
        self.setup_exchange(self.exchange)

    def add_on_channel_close_callback(self):
        """This method tells pika to call the on_channel_closed method if
        RabbitMQ unexpectedly closes the channel."""
        self.debug('Adding channel close callback')
        self.channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reason):
        r"""Actions to perform when the channel is closed. Close the
        connection."""
        self.debug('Channel %i was closed: %s', channel, reason)
        if self.direction == 'recv':
            self.close_connection()
        else:
            self.channel = None
            if not self._closing.has_started():
                self.connection.close()

    # EXCHANGE
    def setup_exchange(self, exchange_name):
        r"""Setup the exchange."""
        self.debug('Declaring exchange %s', exchange_name)
        cb = functools.partial(
            self.on_exchange_declareok, userdata=exchange_name)
        self.channel.exchange_declare(
            exchange=exchange_name,
            auto_delete=True,
            callback=cb)

    def on_exchange_declareok(self, unused_frame, userdata):
        r"""Actions to perform once an exchange is succesfully declared.
        Set up the queue."""
        self.debug('Exchange declared: %s', userdata)
        self.setup_queue(self.queue)

    # QUEUE
    def setup_queue(self, queue_name):
        r"""Set up the message queue."""
        self.debug('Declaring queue %s', queue_name)
        cb = functools.partial(self.on_queue_declareok, userdata=queue_name)
        self.channel.queue_declare(queue=queue_name, callback=cb,
                                   exclusive=False,
                                   passive=self.queue.startswith('amq.'))

    def on_queue_declareok(self, method_frame, userdata):
        r"""Actions to perform once the queue is succesfully declared. Bind
        the queue."""
        queue_name = userdata
        self.debug('Binding %s to %s', self.exchange, queue_name)
        if not self.queue:
            self.address += method_frame.method.queue
        cb = functools.partial(self.on_bindok, userdata=queue_name)
        self.channel.queue_bind(
            queue_name,
            self.exchange,
            callback=cb)
        
    def on_bindok(self, unused_frame, userdata):
        r"""Actions to perform once the queue is succesfully bound. Start
        consuming messages."""
        self.debug('Queue bound')
        if self.direction == 'recv':
            self.set_qos()
        else:
            self.enable_delivery_confirmations()
            self._opening.stop()  # Ready for sending
            self.debug('Finished opening producer')

    # CONSUMER (RECV) SPECIFIC
    def set_qos(self):
        self.channel.basic_qos(
            prefetch_count=self._prefetch_count,
            callback=self.on_basic_qos_ok)

    def on_basic_qos_ok(self, unused_frame):
        r"""Actions to perform one the qos is set."""
        self.debug('QOS set to: %d', 1)
        self.start_consuming()

    def start_consuming(self):
        self.debug('Issuing consumer related RPC commands')
        self.add_on_cancel_callback()
        self.consumer_tag = self.channel.basic_consume(
            self.queue, self.on_message, auto_ack=True)
        self._consuming.start()
        self._opening.stop()
        self.debug('Finished opening consumer')

    def add_on_cancel_callback(self):
        self.debug('Adding consumer cancellation callback')
        self.channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        self.debug('Consumer was cancelled remotely, shutting down: %r',
                   method_frame)
        self.close_channel()

    def on_channel_closeok(self, _unused_frame):
        self.debug('Channel closed.')

    def on_message(self, _unused_channel, basic_deliver, properties, body):
        r"""Buffer received messages."""
        self.debug('Received message # %s from %s: %.100s',
                   basic_deliver.delivery_tag, properties.app_id, body)
        body = tools.str2bytes(body)
        with self.rmq_lock:
            self._buffered_messages.append(body)
        # Not required because auto_ack is True
        # self.acknowledge_message(basic_deliver.delivery_tag)

    # def acknowledge_message(self, delivery_tag):
    #     self.debug('Acknowledging message %s', delivery_tag)
    #     self.channel.basic_ack(delivery_tag, True)

    def stop_consuming(self):
        if self.channel:
            self.debug('Sending a Basic.Cancel RPC command to RabbitMQ')
            cb = functools.partial(
                self.on_cancelok, userdata=self.consumer_tag)
            self.channel.basic_cancel(self.consumer_tag, cb)

    def on_cancelok(self, unused_frame, userdata):
        r"""Actions to perform after succesfully cancelling consumption. Closes
        the channel."""
        self._consuming.stop()
        self.debug(
            'RabbitMQ acknowledged the cancellation of the consumer: %s',
            userdata)
        self.close_channel()

    # PUBLISHER (SEND) SPECIFIC
    def enable_delivery_confirmations(self):
        r"""Turn on delivery confirmations."""
        self.debug('Issuing Confirm.Select RPC command')
        self.channel.confirm_delivery(self.on_delivery_confirmation)

    def on_delivery_confirmation(self, method_frame):
        r"""Actions performed when a sent message is confirmed."""
        confirmation_type = method_frame.method.NAME.split('.')[1].lower()
        self.debug('Received %s for delivery tag: %i', confirmation_type,
                   method_frame.method.delivery_tag)
        if confirmation_type == 'ack':
            self._acked += 1
        elif confirmation_type == 'nack':
            self._nacked += 1
        self._buffered_messages.remove(method_frame.method.delivery_tag)
        self.debug(
            'Published %i messages, %i have yet to be confirmed, '
            '%i were acked and %i were nacked', self._message_number,
            len(self._buffered_messages), self._acked, self._nacked)
