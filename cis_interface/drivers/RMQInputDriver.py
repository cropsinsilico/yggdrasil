
import json
from StringIO import *
from logging import *
import requests
from RMQConnection import RMQConnection
import time
import os
from pprint import pformat

class RMQInputDriver(RMQConnection):
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
        super(RMQInputDriver, self).__init__(name, "_IN", args, **kwargs)
        self.debug(':args: %s', args)
        self._consumer_tag = None

    def printStatus(self):
        r"""Print the driver status."""
        self.debug('::printStatus')
        super(RMQInputDriver, self).printStatus()
        url = 'http://%s:%s/api/%s/%s/%s' % (self.server, 15672, 'queues', '%2f', self.args)
        res = requests.get(url, auth=(self.user, self.passwd))
        jdata = res.json()
        qdata = jdata.get('message_stats', '')
        self.error(": server info: %s", pformat(qdata))
        # errors just always print

    def start_consuming(self):
        r"""Begin consuming messages and add the callback for cancelling
        consumption."""
        self.debug(': start_consuming')
        self.add_on_cancel_callback()
        self._consumer_tag = self.channel.basic_consume(
            self.on_message, queue=self.args)
        # one at a time, don't stuff the Qs
        self.channel.basic_qos(prefetch_count=1)

    # def on_consumer_cancelled(self, method_frame):
    #     r"""Actions to perform when consumption is cancelled."""
    #     self.debug(': Consumer was cancelled remotely, shutting down: %r',
    #                method_frame)
    #     self._closing = True
    #     if self.channel:
    #        self.channel.close()

    def on_message(self, unused_channel, basic_deliver, properties, body):
        r"""Action to perform when a message is received. Send it to the
        local queue and acknowledge the message."""
        self.debug('::on_message: received message # %s from %s',
                   basic_deliver.delivery_tag, properties.app_id)
        self.ipc_send(body)
        self.acknowledge_message(basic_deliver.delivery_tag)

    def acknowledge_message(self, delivery_tag):
        r"""Acknowledge that a message was received."""
        self.debug(':ack message %s', delivery_tag)
        self.channel.basic_ack(delivery_tag)

    def stop_consuming(self):
        r"""Stop message consumption."""
        if self.channel:
            self.debug('::Sending a Basic.Cancel RPC command to RabbitMQ')
            self.channel.add_on_cancel_callback(self.on_consumer_cancelled)
            self.channel.basic_cancel(self.on_consumer_cancelled, self._consumer_tag)

    # def stop(self):
    #     r"""Stop the driver. Close the connection."""
    #     self.debug('.Stopping')
    #     RMQConnection.stop(self)  
    #     self._closing = True
    #     #self.stop_consuming()
    #     self.debug('.stop returns')

    def on_delete(self):
        r"""Delete the driver. Unbinding and deleting the queue and closing
        the connection."""
        self.debug('::delete')
        try:
            self.channel.queue_unbind(exchange=os.environ['PSI_NAMESPACE'], queue=self.args)
            # self.channel.queue_delete(queue=self.args, if_unused=True)
            # self.connection.close()
        except:
            self.debug("::delete(): exception (IGNORED)")
        self.debug('::delete done')

