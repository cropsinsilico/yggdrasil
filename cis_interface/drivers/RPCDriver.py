from cis_interface.drivers.Driver import Driver
from cis_interface.drivers.CommDriver import CommDriver


class RPCDriver(Driver):
    r"""Base class for any driver that requires to access to input & output
    queues for RPC type functionality.

    Args:
        name (str): The name of the message queue set that the driver should
            connect to. (name + "_IN" and name + "_OUT")
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        icomm (:class:`cis_interface.drivers.CommDriver`): Driver for the input
            message queue.
        ocomm (:class:`cis_interface.drivers.CommDriver`): Driver for the output
            message ueue.

    """
    def __init__(self, name, args=None, **kwargs):
        super(RPCDriver, self).__init__(name, **kwargs)
        self.debug('')
        self.icomm = CommDriver(name, direction='recv', **kwargs)
        self.ocomm = CommDriver(name, direction='send', **kwargs)
        out = {}
        out.update(self.icomm.env)
        out.update(self.ocomm.env)
        self.env = out

    @property
    def comms_open(self):
        r"""bool: True if both input and output comms open."""
        with self.lock:
            return (self.icomm.is_comm_open and self.ocomm.is_comm_open)

    @property
    def is_valid(self):
        r"""bool: True if both comms are open and parent class is valid."""
        with self.lock:
            return (super(RPCDriver, self).is_valid and
                    self.icomm.is_valid and
                    self.ocomm.is_valid)
        
    @property
    def n_msg_in(self):
        r"""int: The number of messages in the input comm."""
        return self.icomm.n_msg

    @property
    def n_msg_out(self):
        r"""int: The number of messages in the output comm."""
        return self.ocomm.n_msg

    def start(self):
        r"""Run the input/output comm drivers."""
        self.debug('')
        self.icomm.start()
        self.ocomm.start()
        super(RPCDriver, self).run()
        self.debug('done')

    def graceful_stop(self):
        r"""Allow the IPC comms to terminate gracefully."""
        self.debug('')
        self.icomm.graceful_stop()
        self.ocomm.graceful_stop()
        super(RPCDriver, self).graceful_stop()

    def close_comms(self):
        r"""Close the IPC comms."""
        self.debug('')
        self.icomm.close_comm()
        self.ocomm.close_comm()

    def do_terminate(self):
        r"""Terminate input/output comm drivers."""
        self.debug('')
        self.icomm.terminate()
        self.ocomm.terminate()
        super(RPCDriver, self).do_terminate()

    def on_model_exit(self):
        r"""Actions to perform when the associated model driver is finished."""
        self.debug('')
        self.ocomm.on_model_exit()
        self.icomm.on_model_exit()
        super(RPCDriver, self).on_model_exit()
        
    def cleanup(self):
        r"""Perform cleanup for IPC drivers."""
        self.debug('')
        self.icomm.cleanup()
        self.ocomm.cleanup()
        super(RPCDriver, self).cleanup()

    def printStatus(self):
        r"""Print information on the status of the driver."""
        super(RPCDriver, self).printStatus()
        self.icomm.printStatus(beg_msg='RPC Input Driver:')
        self.ocomm.printStatus(beg_msg='RPC Ouput Driver:')

    def send(self, data, *args, **kwargs):
        r"""Send message smaller than maxMsgSize to the output comm.

        Args:
            data (str): Message to be sent.
            *args: Arguments are passed to output comm send method.
            **kwargs: Keyword arguments are passed to output comm send method.

        Returns:
           bool: Succes or failure of send.

        """
        return self.ocomm.send(data, *args, **kwargs)

    def recv(self, *args, **kwargs):
        r"""Receive message smaller than maxMsgSize from the input comm.

        Args:
            *args: Arguments are passed to input comm recv method.
            **kwargs: Keyword arguments are passed to input comm recv method.

        Returns:
            tuple (bool, str): Success or failure of recv and the received
                message.

        """
        return self.icomm.recv(*args, **kwargs)
            
    def send_nolimit(self, data, *args, **kwargs):
        r"""Send message larger than maxMsgSize to the input comm.

        Args:
            data (str): Message to be sent.
            *args: Arguments are passed to output comm send_nolimit method.
            **kwargs: Keyword arguments are passed to output comm send_nolimit
                method.

        Returns:
           bool: Succes or failure of send.

        """
        return self.ocomm.send_nolimit(data, *args, **kwargs)

    def recv_nolimit(self, *args, **kwargs):
        r"""Receive message larger than maxMsgSize from the output comm.

        Args:
            *args: Arguments are passed to input comm recv_nolimit method.
            **kwargs: Keyword arguments are passed to input comm recv_nolimit
                method.

        Returns:
            tuple (bool, str): Success or failure of recv and the received
                message.

        """
        return self.icomm.recv_nolimit(*args, **kwargs)
