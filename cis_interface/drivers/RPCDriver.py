from cis_interface.drivers.Driver import Driver
from cis_interface.drivers.IODriver import IODriver


class RPCDriver(Driver):
    r"""Base class for any driver that requires to access to input & output
    queues for RPC type functionality.

    Args:
        name (str): The name of the message queue set that the driver should
            connect to. (name + "_IN" and name + "_OUT")
        \*\*kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    Attributes (in addition to parent class's):
        iipc (:class:`cis_interface.drivers.IODriver`): Driver for the input
            message queue.
        oipc (:class:`cis_interface.drivers.IODriver`): Driver for the output
            message ueue.

    """
    def __init__(self, name, args=None, **kwargs):
        super(RPCDriver, self).__init__(name, **kwargs)
        self.debug()
        self.iipc = IODriver(name, '_IN', **kwargs)
        self.oipc = IODriver(name, '_OUT', **kwargs)
        out = {}
        out.update(self.iipc.env)
        out.update(self.oipc.env)
        self.env = out

    @property
    def queues_open(self):
        r"""bool: True if both input and output queues open."""
        with self.lock:
            return (self.iipc.queue_open and self.oipc.queue_open)

    @property
    def is_valid(self):
        r"""bool: True if both queues are open and parent class is valid."""
        with self.lock:
            return (super(RPCDriver, self).is_valid and self.queues_open)
        
    @property
    def n_msg_in(self):
        r"""int: The number of messages in the input queue."""
        return self.iipc.n_ipc_msg

    @property
    def n_msg_out(self):
        r"""int: The number of messages in the output queue."""
        return self.oipc.n_ipc_msg

    def run(self):
        r"""Run the input/output queue drivers."""
        super(RPCDriver, self).run()
        self.debug('.run()')
        self.iipc.start()
        self.oipc.start()
        self.debug('.run() done')

    def graceful_stop(self):
        r"""Allow the IPC queues to terminate gracefully."""
        self.debug('.graceful_stop()')
        self.iipc.graceful_stop()
        self.oipc.graceful_stop()
        super(RPCDriver, self).graceful_stop()

    def close_queues(self):
        r"""Close the IPC queues."""
        self.debug('.close_queues()')
        self.iipc.close_queue()
        self.oipc.close_queue()

    def terminate(self):
        r"""Terminate input/output queue drivers."""
        if self._terminated:
            self.debug(':terminated() Driver already terminated.')
            return
        self.debug('.terminate()')
        self.iipc.terminate()
        self.oipc.terminate()
        super(RPCDriver, self).terminate()

    def on_exit(self):
        r"""Actions to perform when the driver is finished."""
        self.debug('.on_exit()')
        self.iipc.on_exit()
        self.oipc.on_exit()
        super(RPCDriver, self).on_exit()

    def on_model_exit(self):
        r"""Actions to perform when the associated model driver is finished."""
        self.debug('.on_model_exit()')
        self.oipc.on_model_exit()
        self.iipc.on_model_exit()
        super(RPCDriver, self).on_model_exit()
        
    def cleanup(self):
        r"""Perform cleanup for IPC drivers."""
        self.debug('.cleanup()')
        self.iipc.cleanup()
        self.oipc.cleanup()
        super(RPCDriver, self).cleanup()

    def printStatus(self):
        r"""Print information on the status of the driver."""
        super(RPCDriver, self).printStatus()
        self.iipc.printStatus(beg_msg='RPC Input Driver:')
        self.oipc.printStatus(beg_msg='RPC Ouput Driver:')

    def ipc_send(self, data, use_input=False):
        r"""Send message smaller than maxMsgSize to the output queue.

        Args:
            data (str): Message to be sent.
            use_input (bool, optional): If True, the message is sent to the
                input queue instead of the output one.

        """
        if use_input:
            self.iipc.ipc_send(data)
        else:
            self.oipc.ipc_send(data)

    def ipc_recv(self, use_output=False):
        r"""Receive message smaller than maxMsgSize from the input queue.

        Args:
            use_output (bool, optional): If True, the message is received from
                the output queue instead of the input one.

        Returns:
            str: The received message.

        """
        if use_output:
            data = self.oipc.ipc_recv()
        else:
            data = self.iipc.ipc_recv()
        return data
            
    def ipc_send_nolimit(self, data, use_input=False):
        r"""Send message larger than maxMsgSize to the input queue.

        Args:
            data (str): Message to be sent.
            use_input (bool, optional): If True, the message is sent to the
                input queue instead of the output one.

        """
        if use_input:
            self.iipc.ipc_send_nolimit(data)
        else:
            self.oipc.ipc_send_nolimit(data)

    def ipc_recv_nolimit(self, use_output=False):
        r"""Receive message larger than maxMsgSize from the output queue.

        Args:
            use_output (bool, optional): If True, the message is received from
                the output queue instead of the input one.

        Returns:
            str: The received message.

        """
        if use_output:
            data = self.oipc.ipc_recv_nolimit()
        else:
            data = self.iipc.ipc_recv_nolimit()
        return data

    def recv_wait(self, use_output=False, timeout=0.0):
        r"""Receive a message smaller than maxMsgSize. This method will wait
        until there is a message in the queue to return or the queue is closed.

        Args:
            use_output (bool, optional): If True, the message is received from
                the output queue instead of the input one.
            timeout (float, optional): Max time that should be waited. Defaults
                to 0 and is infinite.

        Returns:
            str: The received message.

        """
        if use_output:
            data = self.oipc.recv_wait(timeout=timeout)
        else:
            data = self.iipc.recv_wait(timeout=timeout)
        return data

    def recv_wait_nolimit(self, use_output=False, timeout=0.0):
        r"""Receive a message larger than maxMsgSize. This method will wait
        until there is a message in the queue to return or the queue is closed.

        Args:
            use_output (bool, optional): If True, the message is received from
                the output queue instead of the input one.
            timeout (float, optional): Max time that should be waited. Defaults
                to 0 and is infinite.

        Returns:
            str: The received message.

        """
        if use_output:
            data = self.oipc.recv_wait_nolimit(timeout=timeout)
        else:
            data = self.iipc.recv_wait_nolimit(timeout=timeout)
        return data
