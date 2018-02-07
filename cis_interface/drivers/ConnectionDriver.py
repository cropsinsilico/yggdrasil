"""Module for funneling messages from one comm to another."""
import os
import importlib
from cis_interface import backwards
from cis_interface.communication import new_comm
from cis_interface.drivers.Driver import Driver


class ConnectionDriver(Driver):
    r"""Class that continuously passes messages from one comm to another.

    Args:
        name (str): Name that should be used to set names of input/output comms.
        icomm_kws (dict, optional): Keyword arguments for the input communicator.
        ocomm_kws (dict, optional): Keyword arguments for the output communicator.
        translator (str, func, optional): Function or string specifying function
            that should be used to translate messages from the input communicator
            before passing them to the output communicator. If a string, the
            format should be "<package.module>:<function>" so that <function> can
            be imported from <package>. Defaults to None and messages are passed
            directly.
        timeout_send_1st (float, optional): Time in seconds that should be waited
            before giving up on the first send. Defaults to self.timeout.
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
        translator (func): Function that will be used to translate messages from
            the input communicator before passing them to the output communicator.
        timeout_send_1st (float): Time in seconds that should be waited before
            giving up on the first send.

    """
    def __init__(self, name, icomm_kws=None, ocomm_kws=None,
                 translator=None, timeout_send_1st=None, **kwargs):
        super(ConnectionDriver, self).__init__(name, **kwargs)
        if icomm_kws is None:
            icomm_kws = dict()
        if ocomm_kws is None:
            ocomm_kws = dict()
        # Translator
        if isinstance(translator, str):
            pkg_mod = translator.split(':')
            if len(pkg_mod) == 2:
                mod, fun = pkg_mod[:]
            else:
                raise ValueError("Could not parse translator string: %s" % translator)
            modobj = importlib.import_module(mod)
            if not hasattr(modobj, fun):
                raise AttributeError("Module %s has no funciton %s" % (
                    modobj, fun))
            translator = getattr(modobj, fun)
        if (translator is not None) and (not hasattr(translator, '__call__')):
            raise ValueError("Translator %s not callable." % translator)
        # Input communicator
        self.debug("Creating input comm")
        icomm_kws['direction'] = 'recv'
        icomm_kws['dont_open'] = True
        icomm_kws['reverse_names'] = True
        icomm_name = icomm_kws.pop('name', name)
        self.icomm = new_comm(icomm_name, **icomm_kws)
        self.icomm_kws = icomm_kws
        self.env[self.icomm.name] = self.icomm.address
        # Output communicator
        self.debug("Creating output comm")
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
        self._is_input = ('Input' in str(self.__class__))
        self._is_output = ('Output' in str(self.__class__))
        self._eof_sent = False
        if timeout_send_1st is None:
            timeout_send_1st = self.timeout
        self.timeout_send_1st = timeout_send_1st
        self._first_send_done = False
        self._comm_closed = False
        self.translator = translator
        self.nrecv = 0
        self.nproc = 0
        self.nsent = 0
        self.state = 'started'
        self.debug()
        self.debug(80 * '=')
        self.debug('class = %s', self.__class__)
        # self.debug('    env: %s', str(self.env))
        self.debug('    input: name = %s, address = %s',
                   self.icomm.name, self.icomm.address)
        self.debug('    output: name = %s, address = %s',
                   self.ocomm.name, self.ocomm.address)
        self.debug(80 * '=')

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
        self.debug()
        with self.lock:
            if self._comm_closed:
                self.debug('Aborted as comm closed')
                return
            try:
                self.icomm.open()
                self.ocomm.open()
            except BaseException as e:
                self.close_comm()
                raise e
        self.debug('Returning')

    def close_comm(self):
        r"""Close the communicators."""
        self.debug()
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
        self.debug('Returning')

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

    def drain_input(self, timeout=None):
        r"""Wait for the input comm to be empty.

        Args:
            timeout (float, optional): Max time that should be waited. Defaults
                to None and is set to attribute timeout.
            **kwargs: Additional keyword arguments are passed to the parent
                class's graceful_stop method.

        """
        T = self.start_timeout(timeout)
        while ((self.n_msg > 0) and (not T.is_out) and
               (not self.was_terminated)):  # pragma: debug
            self.debug('Draining %d messages', self.n_msg)
            self.sleep()
        self.stop_timeout()
        if self.n_msg > 0:
            self.error("%d messages could not be drained from the input comm.",
                       self.n_msg)

    def drain_output(self, timeout=None):
        r"""Wait for the output comm to be empty.

        Args:
            timeout (float, optional): Max time that should be waited. Defaults
                to None and is set to attribute timeout.
            **kwargs: Additional keyword arguments are passed to the parent
                class's graceful_stop method.

        """
        T = self.start_timeout(timeout)
        while (self.ocomm.n_msg > 0) and (not T.is_out):  # pragma: debug
            self.debug('Draining %d messages', self.ocomm.n_msg)
            self.sleep()
        self.stop_timeout()
        if self.ocomm.n_msg > 0:
            self.error("%d messages could not be drained from the output comm.",
                       self.ocomm.n_msg)

    def graceful_stop(self, timeout=None, **kwargs):
        r"""Stop the driver, first waiting for the input comm to be empty.

        Args:
            timeout (float, optional): Max time that should be waited. Defaults
                to None and is set to attribute timeout.
            **kwargs: Additional keyword arguments are passed to the parent
                class's graceful_stop method.

        """
        self.debug()
        self.drain_input(timeout=timeout)
        self.drain_output(timeout=timeout)
        super(ConnectionDriver, self).graceful_stop()
        self.debug('Returning')

    def on_model_exit(self, close_input=False):
        r"""Drain input and then close it."""
        self.debug()
        if close_input or self._is_output:
            self.drain_input()
            with self.lock:
                self.icomm.close()
            self.info()
        super(ConnectionDriver, self).on_model_exit()

    def do_terminate(self):
        r"""Stop the driver by closing the communicators."""
        self.debug()
        self.close_comm()
        super(ConnectionDriver, self).do_terminate()

    def cleanup(self):
        r"""Ensure that the communicators are closed."""
        self.debug()
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

    def after_loop(self, send_eof=None):
        r"""Actions to perform after sending messages."""
        self.debug()
        # Close input comm in case loop did not
        with self.lock:
            self.icomm.close()
        # Send EOF for output drivers in case the model did not
        if send_eof is None:
            if self._is_input:
                send_eof = False
            elif self._is_output:
                send_eof = True
            else:
                send_eof = False
        if send_eof:
            self.send_eof()
        # Close output comm after waiting for output to be processed
        self.drain_output()
        if self.ocomm.n_msg > 0:
            self.error("%d messages could not be drained from the output comm.",
                       self.ocomm.n_msg)
        self.ocomm.linger_on_close = True
        self.close_comm()

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
        self.debug('EOF received')
        self.send_eof()
        return False

    def on_message(self, msg):
        r"""Process a message.

        Args:
            msg (bytes, str): Message to be processed.

        Returns:
            bytes, str: Processed message.

        """
        if self.translator is None:
            return msg
        else:
            return self.translator(msg)

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
        T = self.start_timeout(self.timeout_send_1st)
        flag = self._send_message(*args, **kwargs)
        self.ocomm.suppress_special_debug = True
        if not flag:
            self.debug("1st send failed, will keep trying for %f s in silence.",
                       float(self.timeout_send_1st))
        while (not T.is_out) and (not flag) and self.ocomm.is_open:
            flag = self._send_message(*args, **kwargs)
            if not flag:
                self.sleep()
        self.stop_timeout()
        self.ocomm.suppress_special_debug = False
        self._first_send_done = True
        if not flag:
            self.error("1st send failed.")
        else:
            self.debug("1st send succeded")
        return flag

    def send_eof(self):
        r"""Send EOF message.

        Returns:
            bool: Success or failure of send.

        """
        self.debug()
        if not self._eof_sent:
            out = self.send_message(self.ocomm.eof_msg)
            self._eof_sent = True
        else:
            out = False
        return out

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
        self.debug('Running in %s', os.getcwd())
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
                self.debug('No more messages')
                break
            if isinstance(msg, backwards.bytes_type) and len(msg) == 0:
                self.state = 'waiting'
                self.verbose_debug(':run: Waiting for next message.')
                self.sleep()
                continue
            self.nrecv += 1
            self.state = 'received'
            self.debug('Received message that is %d bytes from %s.',
                       len(msg), self.icomm.address)
            # Process message
            self.state = 'processing'
            msg = self.on_message(msg)
            if msg is False:  # pragma: debug
                self.debug('Could not process message.')
                break
            elif len(msg) == 0:
                self.debug('Message skipped.')
                continue
            self.nproc += 1
            self.state = 'processed'
            self.debug('Processed message.')
            # Send a message
            self.state = 'sending'
            ret = self.send_message(msg)
            if ret is False:
                self.debug('Could not send message.')
                break
            self.nsent += 1
            self.state = 'sent'
            self.debug('Sent message to %s.', self.ocomm.address)
        # Perform post-loop follow up
        self.after_loop()
        self.debug('Received %d messages, processed %d, sent %d.',
                   self.nrecv, self.nproc, self.nsent)
