import json
from logging import *
import requests
from RMQConnection import RMQConnection
import os
from threading import Thread

class RMQOutputDriver(RMQConnection):
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
        debug("RMQOutputDriver(%s, %s)", name, args)
        RMQConnection.__init__(self, name, "_OUT", args, **kwargs)

    def printStatus(self):
        r"""Print the driver status."""
        self.debug('::printStatus():')
        try:
            super(RMQOutputDriver, self).printStatus()
            print '%-30s' % ('RMQOutputDriver(' + self.name + ')'),
            print '%-30s' % (str(self.queue.method.message_count) +
                             ' in server queue')
        except:
            self.debug("::printStatus(): queue count exception handled")
        self.debug("::printStatus():")

    def start_consuming(self):
        r"""Start publishing messages from the local queue."""
        self.debug("::start_consuming")
        self.add_on_cancel_callback()
        self.connection.add_timeout(self.sleeptime,
                                    self.publish_message)
        self.publish_message()
    
    def publish_message(self):
        r"""Continue receiving messages from the local queue and passing them 
        to the RabbitMQ server until the queue is closed."""
        while True:
            self.debug(".publish_message(): IPC recv")
            data = self.ipc_recv()
            if data is None:
                self.debug(".publish_message(): queue closed!")
                break
            elif len(data) == 0:
                self.debug(".publish_message(): no data, reschedule")
                self.connection.add_timeout(self.sleeptime,
                                            self.publish_message)
                break
            self.debug(".publish_message(): IPC recv got %d bytes", len(data))
            self.debug(".publish_message(): send %d bytes to AMQP", len(data))
            self.channel.basic_publish(
                exchange=os.environ['PSI_NAMESPACE'],
                routing_key=self.args, body=data, mandatory=True)
            self.debug(".publish_message(): sent to AMQP")
        self.debug(".publish_message returns")

    # def on_delete(self):
    #     r"""Delete the driver. Deleting the queue and closing the connection."""
    #     # self.info(".delete()")
    #     self.debug(".delete()")
    #     try:
    #         pass
    #         # self.channel.queue_unbind(exchange=os.environ['PSI_NAMESPACE'], queue=self.args)
    #         # self.channel.queue_delete(queue=self.args, if_unused=True)
    #         # self.connection.close()
    #     except:
    #         self.debug(".delete(): exception (IGNORED)")
    #     self.debug(".delete() returns")

