from cis_interface.drivers.Driver import Driver
from cis_interface.communication import new_comm


DEBUG_SLEEPS = True


class CommDriver(Driver):
    r"""Base driver for any driver that does communication.

    Args:
        name (str): The name of the message queue that the driver should
            connect to.
        **kwargs: Additional keyword arguments are passed to the parent and comm
            classes.

    Attributes:
        comm_name (str): Name of communication class.
        comm (CommBase): Instance of communication class.
        state (str): Description of the last operation performed by the driver.
        numSent (int): The number of messages sent to the queue.
        numReceived (int): The number of messages received from the queue.

    """
    def __init__(self, name, **kwargs):
        super(CommDriver, self).__init__(name, **kwargs)
        self.debug('')
        self.state = 'Started'
        self.numSent = 0
        self.numReceived = 0
        kwargs.setdefault('reverse_names', True)
        self.comm = None
        self.comm = new_comm(name, dont_open=True, **kwargs)
        self.comm_name = self.comm.comm_class
        for k, v in self.comm.opp_comms.items():
            self.env[k] = v
        self.debug(".env: %s", self.env)

    @property
    def maxMsgSize(self):
        r"""int: Maximum message size."""
        return self.comm.maxMsgSize

    @property
    def is_valid(self):
        r"""bool: Returns True if the connection is open and the parent class
        is valid."""
        with self.lock:
            return (super(CommDriver, self).is_valid and self.is_comm_open)

    @property
    def is_comm_open(self):
        r"""bool: Returns True if the connection is open."""
        with self.lock:
            return self.comm.is_open

    @property
    def is_comm_closed(self):
        r"""bool: Returns True if the connection is closed."""
        with self.lock:
            return self.comm.is_closed

    @property
    def n_msg(self):
        r"""int: The number of messages in the queue."""
        with self.lock:
            return self.comm.n_msg

    def open_comm(self):
        r"""Open the queue."""
        self.debug('')
        with self.lock:
            self.comm.open()
        self.debug('Returning')
        
    def close_comm(self):
        r"""Close the queue."""
        self.debug('')
        if self.comm is not None:
            with self.lock:
                self.comm.close()
        self.debug('Returning')

    def start(self):
        r"""Open connection before running."""
        if self.comm_name != 'CommBase':
            self.open_comm()
            Tout = self.start_timeout()
            while (not self.is_comm_open) and (not Tout.is_out):
                self.sleep()
            self.stop_timeout()
            if not self.is_comm_open:
                raise Exception("Connection never finished opening.")
        super(CommDriver, self).start()
        
    def graceful_stop(self, timeout=None, **kwargs):
        r"""Stop the CommDriver, first draining the message queue.

        Args:
            timeout (float, optional): Max time that should be waited. Defaults
                to None and is set to attribute timeout. If 0, it will never
                timeout.
            \*\*kwargs: Additional keyword arguments are passed to the parent
                class's graceful_stop method.

        """
        self.debug('')
        T = self.start_timeout(timeout)
        try:
            while (self.n_msg > 0) and (not T.is_out):  # pragma: debug
                if DEBUG_SLEEPS:
                    self.debug('Draining %d messages', self.n_msg)
                self.sleep()
        except Exception as e:  # pragma: debug
            self.raise_error(e)
        self.stop_timeout()
        super(CommDriver, self).graceful_stop()
        self.debug('Returning')

    def do_terminate(self):
        r"""Stop the CommDriver by closing the comm."""
        self.debug('')
        self.close_comm()
        super(CommDriver, self).do_terminate()

    def cleanup(self):
        r"""Ensure that the queues are removed."""
        self.debug('')
        self.close_comm()
        super(CommDriver, self).cleanup()

    def printStatus(self, beg_msg='', end_msg=''):
        r"""Print information on the status of the CommDriver.

        Arguments:
            beg_msg (str, optional): Additional message to print at beginning.
            end_msg (str, optional): Additional message to print at end.

        """
        msg = beg_msg
        msg += '%-30s' % (self.__module__ + '(' + self.name + ')')
        msg += '%-30s' % ('last action: ' + self.state)
        msg += '%-15s' % (str(self.numSent) + ' delivered, ')
        msg += '%-15s' % (str(self.numReceived) + ' accepted, ')
        msg += '%-15s' % (str(self.n_msg) + ' ready')
        msg += end_msg
        print(msg)

    def send(self, data, *args, **kwargs):
        r"""Send a message smaller than maxMsgSize.

        Args:
            str: The message to be sent.
            *args: All arguments are passed to comm send method.
            **kwargs: All keywords arguments are passed to comm send method.

        Returns:
            bool: Success or failure of send.

        """
        with self.lock:
            self.state = 'deliver'
            ret = self.comm.send(data, *args, **kwargs)
            if ret:
                self.state = 'delivered'
                self.numSent = self.numSent + 1
            else:
                self.state = 'delivery failed'
        return ret

    def recv(self, *args, **kwargs):
        r"""Receive a message smaller than maxMsgSize.

        Args:
            *args: All arguments are passed to comm recv method.
            **kwargs: All keywords arguments are passed to comm recv method.

        Returns:
            tuple (bool, str): The success or failure of receiving and the
                received message.

        """
        with self.lock:
            self.state = 'receiving'
            ret = self.comm.recv(*args, **kwargs)
            if ret[0]:
                self.state = 'received'
                self.numReceived += 1
            else:
                self.state = 'received failed'
        return ret

    def send_nolimit(self, data, *args, **kwargs):
        r"""Send a message larger than maxMsgSize in multiple parts.

        Args:
            str: The message to be sent.
            *args: All arguments are passed to comm send_nolimit method.
            **kwargs: All keywords arguments are passed to comm send_nolimit
                method.

        Returns:
            bool: Success or failure of send.

        """
        ret = self.comm.send_nolimit(data, *args, **kwargs)
        return ret

    def recv_nolimit(self, *args, **kwargs):
        r"""Receive a message larger than maxMsgSize in multiple parts.

        Args:
            *args: All arguments are passed to comm recv_nolimit method.
            **kwargs: All keywords arguments are passed to comm recv_nolimit
                method.

        Returns:
            tuple (bool, str): The success or failure of receiving and the
                received message.

        """
        ret = self.comm.recv_nolimit(*args, **kwargs)
        return ret
