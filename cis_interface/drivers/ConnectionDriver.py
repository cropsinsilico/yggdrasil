"""Module for funneling messages from one comm to another."""
import os
from cis_interface import backwards
from cis_interface.communication import new_comm
from cis_interface.drivers.Driver import Driver


class ConnectionDriver(Driver):
    r"""Class that continuously passes messages from one comm to another.

    Args:
        name (str): Name that should be used to set names of input/output comms.
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
    def __init__(self, name, icomm_kws=None, ocomm_kws=None, **kwargs):
        super(ConnectionDriver, self).__init__(name, **kwargs)
        if icomm_kws is None:
            icomm_kws = dict()
        if ocomm_kws is None:
            ocomm_kws = dict()
        # Input communicator
        icomm_kws['direction'] = 'recv'
        icomm_kws['dont_open'] = True
        icomm_kws['reverse_names'] = True
        icomm_name = icomm_kws.pop('name', name)
        self.icomm = new_comm(icomm_name, **icomm_kws)
        self.icomm_kws = icomm_kws
        self.env[self.icomm.name] = self.icomm.address
        # Output communicator
        ocomm_kws['direction'] = 'send'
        ocomm_kws['dont_open'] = True
        ocomm_kws['reverse_names'] = True
        ocomm_name = ocomm_kws.pop('name', name)
        try:
            self.ocomm = new_comm(ocomm_name, **ocomm_kws)
        except BaseException as e:
            self.icomm.close()
            raise e
        self.ocomm_kws = ocomm_kws
        self.env[self.ocomm.name] = self.ocomm.address
        # Attributes
        self._first_send_done = False
        self._comm_closed = False
        self.nrecv = 0
        self.nproc = 0
        self.nsent = 0
        self.state = 'started'
        self.debug()
        if False:
            print(80 * '=')
            print(self.__class__)
            print(self.env)
            print(self.icomm.name, self.icomm.address)
            print(self.ocomm.name, self.ocomm.address)

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
            return (self.icomm.is_open and self.ocomm.is_open and
                    not self._comm_closed)

    @property
    def is_comm_closed(self):
        r"""bool: Returns True if both communicators are closed."""
        with self.lock:
            return self.icomm.is_closed and self.ocomm.is_closed

    @property
    def n_msg(self):
        r"""int: Number of messages waiting in input communicator."""
        with self.lock:
            return self.icomm.n_msg

    def open_comm(self):
        r"""Open the communicators."""
        self.debug(':open_comm()')
        with self.lock:
            if self._comm_closed:
                self.debug(':open_comm(): aborted as comm closed')
                return
            try:
                self.icomm.open()
                self.ocomm.open()
            except BaseException as e:
                self.close_comm()
                raise e
        self.debug(':open_comm(): done')

    def close_comm(self):
        r"""Close the communicators."""
        self.debug(':close_comm()')
        with self.lock:
            self._comm_closed = True
            # Capture errors for both comms
            ie = None
            oe = None
            try:
                if getattr(self, 'icomm', None) is not None:
                    self.icomm.close()
            except BaseException as e:
                ie = e
            try:
                if getattr(self, 'ocomm', None) is not None:
                    self.ocomm.close()
            except BaseException as e:
                oe = e
            if ie:
                raise ie
            if oe:
                raise oe
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
        while (self.n_msg > 0) and (not T.is_out):  # pragma: debug
            self.debug('.graceful_stop(): draining %d messages',
                       self.n_msg)
            self.sleep()
        self.stop_timeout()
        super(ConnectionDriver, self).graceful_stop()
        self.debug('.graceful_stop(): done')

    # def on_model_exit(self):
    #     r"""Close the comms."""
    #     self.close_comm()
    #     super(ConnectionDriver, self).on_model_exit()

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
        self.sleep()  # Help ensure senders/receivers connected before messages

    def after_loop(self):
        r"""Actions to perform after sending messages."""
        pass

    def recv_message(self, **kwargs):
        r"""Get a new message to send.

        Args:
            **kwargs: Additional keyword arguments are passed to the appropriate
                recv method.

        Returns:
            str, bool: False if no more messages, message otherwise.

        """
        kwargs.setdefault('timeout', 0)
        with self.lock:
            if self.icomm.is_closed:
                return False
            flag, msg = self.icomm.recv(**kwargs)
        if msg == self.icomm.eof_msg:
            return self.on_eof()
        if flag:
            return msg
        else:
            return flag

    def on_eof(self):
        r"""Actions to take when EOF received.

        Returns:
            str, bool: Value that should be returned by recv_message on EOF.

        """
        self.debug(': EOF received')
        self.send_message(self.ocomm.eof_msg)
        return False

    def on_message(self, msg):
        r"""Process a message.

        Args:
            msg (bytes, str): Message to be processed.

        Returns:
            bytes, str: Processed message.

        """
        return msg

    def _send_message(self, *args, **kwargs):
        r"""Send a single message.

        Args:
            *args: Arguments are passed to the output comm send method.
            *kwargs: Keyword arguments are passed to the output comm send method.

        Returns:
            bool: Success or failure of send.

        """
        with self.lock:
            if self.ocomm.is_closed:
                return False
            flag = self.ocomm.send(*args, **kwargs)
            return flag
        
    def _send_1st_message(self, *args, **kwargs):
        r"""Send the first message, trying multiple times.

        Args:
            *args: Arguments are passed to the output comm send method.
            *kwargs: Keyword arguments are passed to the output comm send method.

        Returns:
            bool: Success or failure of send.

        """
        self.ocomm._first_send_done = True
        flag = False
        T = self.start_timeout()
        while (not T.is_out) and (not flag) and self.ocomm.is_open:
            flag = self._send_message(*args, **kwargs)
        self.stop_timeout()
        self._first_send_done = True
        return flag

    def send_message(self, *args, **kwargs):
        r"""Send a single message.

        Args:
            *args: Arguments are passed to the output comm send method.
            *kwargs: Keyword arguments are passed to the output comm send method.

        Returns:
            bool: Success or failure of send.

        """
        if self._first_send_done:
            flag = self._send_message(*args, **kwargs)
        else:
            flag = self._send_1st_message(*args, **kwargs)
        return flag

    def run(self):
        r"""Run the driver. Continue looping over messages until there are not
        any left or the communication channel is closed.
        """
        self.debug(':run in %s', os.getcwd())
        try:
            self.before_loop()
        except BaseException:  # pragma: debug
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
            if isinstance(msg, backwards.bytes_type) and len(msg) == 0:
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
            if msg is False:  # pragma: debug
                self.debug(':run: Could not process message.')
                break
            elif len(msg) == 0:
                self.debug(':run: Message skipped.')
                continue
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
