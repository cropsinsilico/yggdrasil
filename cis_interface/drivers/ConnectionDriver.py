import os
from cis_interface.communication import new_comm
from cis_interface.drivers.Driver import Driver


class ConnectionDriver(Driver):
    r"""Class that continuously passes messages from one comm to another.

    Args:
        name (str): Name of the queue that messages should be sent to.
        icomm_kws (dict, optional): Keyword arguments for the input communicator.
        ocomm_kws (dict, optional): Keyword arguments for the output communicator.
        **kwargs: Additonal keyword arguments are passed to the parent class.

    Attributes:
        icomm_kws (dict): Keyword arguments for the input communicator.
        ocomm_kws (dict): Keyword arguments for the output communicator.
        icomm (CommBase): Input communicator.
        ocomm (CommBase): Output communicator.
        nrecv (int): Number of messages received.
        nproc (int): Number of messages processed.
        nsent (int): Number of messages sent.
        state (str): Descriptor of last action taken.

    """
    def __init__(self, name, icomm_kws={}, ocomm_kws={}, **kwargs):
        super(ConnectionDriver, self).__init__(name, **kwargs)
        # Input communicator
        icomm_kws['direction'] = 'recv'
        icomm_kws['dont_open'] = True
        self.icomm = new_comm(name, **icomm_kws)
        self.icomm_kws = icomm_kws
        # Output communicator
        ocomm_kws['direction'] = 'send'
        ocomm_kws['dont_open'] = True
        self.ocomm = new_comm(name, **ocomm_kws)
        self.ocomm_kws = ocomm_kws
        # Attributes
        self.nrecv = 0
        self.nproc = 0
        self.nsent = 0
        self.state = 'started'
        self.debug()

    @property
    def is_valid(self):
        r"""bool: Returns True if the connection is open and the parent class
        is valid."""
        with self.lock:
            return (super(ConnectionDriver, self).is_valid and self.is_comm_open)

    @property
    def is_comm_open(self):
        r"""bool: Returns True if both communicators are open."""
        with self.lock:
            return self.icomm.is_open and self.ocomm.is_open

    @property
    def is_comm_closed(self):
        r"""bool: Returns True if both communicators are closed."""
        with self.lock:
            return self.icomm.is_closed and self.ocomm.is_closed

    @property
    def n_msg(self):
        r"""int: Number of messages waiting in input communicator."""
        return self.icomm.n_msg

    def open_comm(self):
        r"""Open the communicators."""
        self.debug(':open_comm()')
        with self.lock:
            self.icomm.open()
            self.ocomm.open()
        self.debug(':open_comm(): done')

    def close_comm(self):
        r"""Close the communicators."""
        self.debug(':close_comm()')
        with self.lock:
            self.icomm.close()
            self.ocomm.close()
        self.debug(':close_comm(): done')

    def start(self):
        r"""Open connection before running."""
        self.open_comm()
        Tout = self.start_timeout()
        while (not self.is_comm_open) and (not Tout.is_out):
            self.sleep()
        self.stop_timeout()
        if not self.is_comm_open:
            raise Exception("Connection never finished opening.")
        super(ConnectionDriver, self).start()

    def graceful_stop(self, timeout=None, **kwargs):
        r"""Stop the driver, first waiting for the input comm to be empty.

        Args:
            timeout (float, optional): Max time that should be waited. Defaults
                to None and is set to attribute timeout.
            **kwargs: Additional keyword arguments are passed to the parent
                class's graceful_stop method.

        """
        self.debug('.graceful_stop()')
        T = self.start_timeout(timeout)
        while (self.n_msg > 0) and (not T.is_out):
            if DEBUG_SLEEPS:
                self.debug('.graceful_stop(): draining %d messages',
                           self.n_msg)
                self.sleep()
        self.stop_timeout()
        super(ConnectionDriver, self).graceful_stop()
        self.debug('.graceful_stop(): done')

    def terminate(self):
        r"""Stop the driver, closing the communicators."""
        if self._terminated:
            self.debug(':terminated() Driver already terminated.')
            return
        self.debug(':terminate()')
        self.close_comm()
        super(ConnectionDriver, self).terminate()
        self.debug(':terminate(): done')

    def cleanup(self):
        r"""Ensure that the communicators are closed."""
        self.debug(':cleanup()')
        self.close_comm()
        super(ConnectionDriver, self).cleanup()

    def printStatus(self, beg_msg='', end_msg=''):
        r"""Print information on the status of the ConnectionDriver.

        Arguments:
            beg_msg (str, optional): Additional message to print at beginning.
            end_msg (str, optional): Additional message to print at end.

        """
        msg = beg_msg
        msg += '%-30s' % (self.__module__ + '(' + self.name + ')')
        msg += '%-30s' % ('last action: ' + self.state)
        msg += '%-15s' % (str(self.nrecv) + ' received, ')
        msg += '%-15s' % (str(self.nproc) + ' processed, ')
        msg += '%-15s' % (str(self.nsent) + ' sent, ')
        msg += '%-15s' % (str(self.n_msg) + ' ready')
        msg += end_msg
        print(msg)

    def before_loop(self):
        r"""Actions to perform prior to sending messages."""
        self.open_comm()

    def after_loop(self):
        r"""Actions to perform after sending messages."""
        self.close_comm()

    def recv_message(self):
        r"""Get a new message to send.

        Returns:
            str, bool: False if no more messages, message otherwise.

        """
        flag, msg = self.icomm.recv(timeout=False)
        if flag:
            return msg
        else:
            return flag

    def on_message(self, msg):
        r"""Process a message.

        Args:
            msg (bytes, str): Message to be processed.

        Returns:
            bytes, str: Processed message.

        """
        return msg

    def send_message(self, msg):
        r"""Send a single message.

        Args:
            msg (str): Message to be sent.

        Returns:
            bool: Success or failure of send.

        """
        return self.ocomm.send(msg)

    def run(self):
        r"""Run the driver. Continue looping over messages until there are not
        any left or the communication channel is closed.
        """
        self.debug(':run in %s', os.getcwd())
        try:
            self.before_loop()
        except:  # pragma: debug
            self.exception('Could not prep for loop.')
            self.close_comm()
            return
        while self.is_valid:
            # Receive a message
            self.state = 'receiving'
            msg = self.recv_message()
            if msg is False:
                self.debug(':run: No more messages')
                break
            if len(msg) == 0:
                self.state = 'waiting'
                self.debug(':run: Waiting for next message.')
                self.sleep()
                continue
            self.nrecv += 1
            self.state = 'received'
            self.debug(':run: Received message that is %d bytes.', len(msg))
            # Process message
            self.state = 'processing'
            msg = self.on_message(msg)
            if msg is False:
                self.debug(':run: Could not process message.')
                break
            self.nproc += 1
            self.state = 'processed'
            self.debug(':run: Processed message.')
            # Send a message
            self.state = 'sending'
            ret = self.send_message(msg)
            if ret is False:
                self.debug(':run: Could not send message.')
                break
            self.nsent += 1
            self.state = 'sent'
            self.debug(':run: Sent message.')
        # Perform post-loop follow up
        self.after_loop()
        self.debug(':run: Received %d messages, processed %d, sent %d.',
                   self.nrecv, self.nproc, self.nsent)
