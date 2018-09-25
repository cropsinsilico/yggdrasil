"""Module for funneling messages from one comm to another."""
import os
import numpy as np
import threading
from cis_interface import backwards
from cis_interface.communication import new_comm, get_comm_class
from cis_interface.drivers.Driver import Driver
from cis_interface.schema import register_component, str_to_function


@register_component
class ConnectionDriver(Driver):
    r"""Class that continuously passes messages from one comm to another.

    Args:
        name (str): Name that should be used to set names of input/output comms.
        icomm_kws (dict, optional): Keyword arguments for the input communicator.
        ocomm_kws (dict, optional): Keyword arguments for the output communicator.
        translator (str, func, optional): Function or string specifying function
            that should be used to translate messages from the input communicator
            before passing them to the output communicator. If a string, the
            format should be "<package.module>:<function>" so that <function>
            can be imported from <package>. Defaults to None and messages are
            passed directly. This can also be a list of functions/strings that
            will be called on the messages in the order they are provided.
        timeout_send_1st (float, optional): Time in seconds that should be
            waited before giving up on the first send. Defaults to self.timeout.
        single_use (bool, optional): If True, the driver will be stopped after
            one loop. Defaults to False.
        onexit (str, optional): Class method that should be called when the
            corresponding model exits, but before the driver is shut down.
            Defaults to None.
        **kwargs: Additonal keyword arguments are passed to the parent class.

    Attributes:
        icomm_kws (dict): Keyword arguments for the input communicator.
        ocomm_kws (dict): Keyword arguments for the output communicator.
        icomm (CommBase): Input communicator.
        ocomm (CommBase): Output communicator.
        nrecv (int): Number of messages received.
        nproc (int): Number of messages processed.
        nsent (int): Number of messages sent.
        nskip (int): Number of messages skipped.
        state (str): Descriptor of last action taken.
        translator (func): Function that will be used to translate messages from
            the input communicator before passing them to the output communicator.
        timeout_send_1st (float): Time in seconds that should be waited before
            giving up on the first send.
        single_use (bool): If True, the driver will be stopped after one
            loop.
        onexit (str): Class method that should be called when the corresponding
            model exits, but before the driver is shut down.

    """
    
    _icomm_type = 'DefaultComm'
    _ocomm_type = 'DefaultComm'
    _schema_type = 'connection'
    _schema = {'input': {'type': ['string', 'list'], 'required': True,
                         'schema': {'type': 'string'},
                         'excludes': 'input_file'},
               'input_file': {'required': True, 'type': 'dict',
                              'excludes': 'input', 'schema': 'file'},
               'output': {'type': ['string', 'list'], 'required': True,
                          'schema': {'type': 'string'},
                          'excludes': 'output_file'},
               'output_file': {'required': True, 'type': 'dict',
                               'excludes': 'output', 'schema': 'file'},
               'translator': {'type': ['function', 'list'],
                              'schema': {'type': 'function'},
                              'required': False},
               'onexit': {'type': 'string', 'required': False}}
    _is_input = False
    _is_output = False

    @classmethod
    def direction(cls):
        r"""Get direction of connection."""
        if cls._is_input:
            out = 'input'
        elif cls._is_output:
            out = 'output'
        else:
            out = None
        return out

    def __init__(self, name, translator=None, timeout_send_1st=None,
                 single_use=False, onexit=None, **kwargs):
        super(ConnectionDriver, self).__init__(name, **kwargs)
        # Translator
        if translator is None:
            translator = []
        elif not isinstance(translator, list):
            translator = [translator]
        self.translator = []
        for t in translator:
            if isinstance(t, str):
                t = str_to_function(t)
            if not hasattr(t, '__call__'):
                raise ValueError("Translator %s not callable." % t)
            self.translator.append(t)
        if (onexit is not None) and (not hasattr(self, onexit)):
            raise ValueError("onexit '%s' is not a class method." % onexit)
        self.onexit = onexit
        # Attributes
        self._eof_sent = False
        if timeout_send_1st is None:
            timeout_send_1st = self.timeout
        self.single_use = single_use
        self.timeout_send_1st = timeout_send_1st
        self._first_send_done = False
        self._comm_opened = threading.Event()
        self._comm_closed = False
        self._used = False
        self._skip_after_loop = False
        self._model_exited = False
        self.nrecv = 0
        self.nproc = 0
        self.nsent = 0
        self.nskip = 0
        self.state = 'started'
        self.close_state = ''
        # Add comms and print debug info
        self._init_comms(name, **kwargs)
        self.debug('')
        self.debug(80 * '=')
        self.debug('class = %s', self.__class__)
        # self.debug('    env: %s', str(self.env))
        self.debug('    input: name = %s, address = %s',
                   self.icomm.name, self.icomm.address)
        self.debug('    output: name = %s, address = %s',
                   self.ocomm.name, self.ocomm.address)
        self.debug(80 * '=')

    def _init_comms(self, name, icomm_kws=None, ocomm_kws=None, **kwargs):
        r"""Parse keyword arguments for input/output comms."""
        if icomm_kws is None:
            icomm_kws = dict()
        if ocomm_kws is None:
            ocomm_kws = dict()
        # Input communicator
        self.debug("Creating input comm")
        icomm_kws['direction'] = 'recv'
        icomm_kws['dont_open'] = True
        icomm_kws['reverse_names'] = True
        icomm_kws['close_on_eof_recv'] = False
        icomm_kws.setdefault('comm', self._icomm_type)
        icomm_kws.setdefault('name', name)
        if self._is_input:
            ikws = get_comm_class(icomm_kws['comm'])._schema
            for k in ikws:
                if (k not in icomm_kws) and (k in kwargs):
                    icomm_kws[k] = kwargs[k]
        self.icomm = new_comm(icomm_kws.pop('name'), **icomm_kws)
        self.icomm_kws = icomm_kws
        self.env.update(**self.icomm.opp_comms)
        # Output communicator
        self.debug("Creating output comm")
        ocomm_kws['direction'] = 'send'
        ocomm_kws['dont_open'] = True
        ocomm_kws['reverse_names'] = True
        ocomm_kws.setdefault('comm', self._ocomm_type)
        ocomm_kws.setdefault('name', name)
        if self._is_output:
            okws = get_comm_class(ocomm_kws['comm'])._schema
            for k in okws:
                if (k not in ocomm_kws) and (k in kwargs):
                    ocomm_kws[k] = kwargs[k]
        try:
            self.ocomm = new_comm(ocomm_kws.pop('name'), **ocomm_kws)
        except BaseException:
            self.icomm.close()
            raise
        self.ocomm_kws = ocomm_kws
        self.env.update(**self.ocomm.opp_comms)
        
    def wait_for_route(self, timeout=None):
        r"""Wait until messages have been routed."""
        T = self.start_timeout(timeout)
        while ((not T.is_out) and
               (self.nrecv != (self.nsent + self.nskip))):  # pragma: debug
            self.sleep()
        self.stop_timeout()
        return (self.nrecv == (self.nsent + self.nskip))

    @property
    def is_valid(self):
        r"""bool: Returns True if the connection is open and the parent class
        is valid."""
        with self.lock:
            return (super(ConnectionDriver, self).is_valid and
                    self.is_comm_open and not (self.single_use and self._used))

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
            return self.icomm.n_msg_recv

    def open_comm(self):
        r"""Open the communicators."""
        self.debug('')
        with self.lock:
            if self._comm_closed:
                self.debug('Aborted as comm closed')
                return
            try:
                self.icomm.open()
                self.ocomm.open()
            except BaseException:
                self.close_comm()
                raise
            self._comm_opened.set()
        self.debug('Returning')

    def close_comm(self):
        r"""Close the communicators."""
        self.debug('')
        with self.lock:
            self._comm_closed = True
            self._skip_after_loop = True
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

    def graceful_stop(self, timeout=None, **kwargs):
        r"""Stop the driver, first waiting for the input comm to be empty.

        Args:
            timeout (float, optional): Max time that should be waited. Defaults
                to None and is set to attribute timeout.
            **kwargs: Additional keyword arguments are passed to the parent
                class's graceful_stop method.

        """
        self.debug('')
        with self.lock:
            self.set_close_state('stop')
            self._skip_after_loop = True
        self.drain_input(timeout=timeout)
        self.wait_for_route(timeout=timeout)
        self.drain_output(timeout=timeout)
        super(ConnectionDriver, self).graceful_stop()
        self.debug('Returning')

    def on_model_exit(self):
        r"""Drain input and then close it."""
        self.debug('')
        if (self.onexit not in [None, 'on_model_exit', 'pass']):
            self.debug("Calling onexit = '%s'" % self.onexit)
            getattr(self, self.onexit)()
        self.drain_input(timeout=self.timeout)
        self.set_close_state('model exit')
        self.debug('Model exit triggered close')
        if self._is_input:
            with self.lock:
                self.icomm.close()
                self.ocomm.close()
        if self._is_output:
            self.wait_for_route(timeout=self.timeout)
            with self.lock:
                self.icomm.close()
        self.set_break_flag()
        self.wait()
        self.debug('Finished')
        super(ConnectionDriver, self).on_model_exit()

    def do_terminate(self):
        r"""Stop the driver by closing the communicators."""
        self.debug('')
        self.set_close_state('terminate')
        self.close_comm()
        super(ConnectionDriver, self).do_terminate()

    def cleanup(self):
        r"""Ensure that the communicators are closed."""
        self.debug('')
        self.close_comm()
        super(ConnectionDriver, self).cleanup()

    def printStatus(self, beg_msg='', end_msg=''):
        r"""Print information on the status of the ConnectionDriver.

        Arguments:
            beg_msg (str, optional): Additional message to print at beginning.
            end_msg (str, optional): Additional message to print at end.

        """
        msg = beg_msg
        msg += '%-50s' % (self.__module__.split('.')[-1] + '(' + self.name + '): ')
        msg += '%-30s' % ('last action: ' + self.state)
        msg += '%-25s' % ('is_open(%s, %s), ' % (self.icomm.is_open,
                                                 self.ocomm.is_open))
        msg += '%-15s' % (str(self.nrecv) + ' received, ')
        msg += '%-15s' % (str(self.nproc) + ' processed, ')
        msg += '%-15s' % (str(self.nskip) + ' skipped, ')
        msg += '%-15s' % (str(self.nsent) + ' sent, ')
        msg += '%-20s' % (str(self.icomm.n_msg) + ' ready to recv')
        msg += '%-20s' % (str(self.ocomm.n_msg) + ' ready to send')
        with self.lock:
            if self.close_state:
                msg += '%-30s' % ('close state: ' + self.close_state)
        msg += end_msg
        print(msg)

    def confirm_input(self, timeout=None):
        r"""Confirm receipt of messages from input comm."""
        T = self.start_timeout(timeout)
        while not T.is_out:  # pragma: debug
            with self.lock:
                if (not self.icomm.is_open):
                    break
                elif self.icomm.is_confirmed_recv:
                    break
            self.sleep(10 * self.sleeptime)
        self.stop_timeout()

    def confirm_output(self, timeout=None):
        r"""Confirm receipt of messages from output comm."""
        T = self.start_timeout(timeout)
        while not T.is_out:  # pragma: debug
            with self.lock:
                if (not self.ocomm.is_open):
                    break
                elif self.ocomm.is_confirmed_send:
                    break
            self.sleep(10 * self.sleeptime)
        self.stop_timeout()

    def drain_input(self, timeout=None):
        r"""Drain messages from input comm."""
        T = self.start_timeout(timeout)
        while not T.is_out:
            with self.lock:
                if (not self.icomm.is_open):
                    break
                elif ((self.icomm.n_msg_recv_drain == 0) and
                      self.icomm.is_confirmed_recv):
                    break
            self.sleep()
        self.stop_timeout()

    def drain_output(self, timeout=None):
        r"""Drain messages from output comm."""
        T = self.start_timeout(timeout)
        while not T.is_out:
            with self.lock:
                if (not self.ocomm.is_open):
                    break
                elif ((self.ocomm.n_msg_send_drain == 0) and
                      self.ocomm.is_confirmed_send):
                    break
            self.sleep()
        self.stop_timeout()

    def before_loop(self):
        r"""Actions to perform prior to sending messages."""
        self.state = 'before loop'
        try:
            self.open_comm()
            self.sleep()  # Help ensure senders/receivers connected before messages
            self.debug('Running in %s, is_valid = %s', os.getcwd(), str(self.is_valid))
            assert(self.is_valid)
        except BaseException:  # pragma: debug
            self.printStatus()
            self.exception('Could not prep for loop (is_open = (%s, %s)).' % (
                self.icomm.is_open, self.ocomm.is_open))
            self.close_comm()
            self.set_break_flag()

    def after_loop(self):
        r"""Actions to perform after sending messages."""
        self.state = 'after loop'
        self.debug('')
        # Close input comm in case loop did not
        self.confirm_input(timeout=False)
        self.debug('Confirmed input')
        with self.lock:
            self.debug('Acquired lock')
            if self._skip_after_loop:
                self.debug("After loop skipped.")
                return
            self.icomm.close()
        # Send EOF in case the model didn't
        if not self.single_use:
            self.send_eof()
        # Do not close output comm in case model/connection still receiving
        self.debug('Finished')

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
        if isinstance(msg, backwards.bytes_type) and (msg == self.icomm.eof_msg):
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
        with self.lock:
            self.debug('EOF received')
            self.state = 'eof'
            self.set_close_state('eof')
            self.set_break_flag()
        self.debug('After EOF')
        return False

    def on_message(self, msg):
        r"""Process a message.

        Args:
            msg (bytes, str): Message to be processed.

        Returns:
            bytes, str: Processed message.

        """
        if (self.ocomm._send_serializer):
            self.update_serializer(msg)
        for t in self.translator:
            msg = t(msg)
        return msg

    def update_serializer(self, msg):
        r"""Update the serializer for the output comm based on input."""
        if self.ocomm.serializer.serializer_type == 0:
            old_kwargs = self.ocomm.serializer.serializer_info
            del old_kwargs['stype']
            self.ocomm.serializer = self.icomm.serializer
            self.ocomm.serializer.update_serializer(**old_kwargs)

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
        self.ocomm._multiple_first_send = False
        T = self.start_timeout(self.timeout_send_1st)
        flag = self._send_message(*args, **kwargs)
        self.ocomm.suppress_special_debug = True
        if not flag:
            self.debug("1st send failed, will keep trying for %f s in silence.",
                       float(self.timeout_send_1st))
        while ((not T.is_out) and (not flag) and
               self.ocomm.is_open):  # pragma: debug
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
        with self.lock:
            if self._eof_sent:  # pragma: debug
                self.debug('Already sent EOF')
                return False
            self._eof_sent = True
        self.debug('Sent EOF')
        return self.send_message(self.ocomm.eof_msg, is_eof=True)

    def send_message(self, *args, **kwargs):
        r"""Send a single message.

        Args:
            *args: Arguments are passed to the output comm send method.
            *kwargs: Keyword arguments are passed to the output comm send method.

        Returns:
            bool: Success or failure of send.

        """
        self.debug('')
        kwargs.pop('is_eof', False)
        with self.lock:
            self._used = True
        if self._first_send_done:
            flag = self._send_message(*args, **kwargs)
        else:
            flag = self._send_1st_message(*args, **kwargs)
        # if self.single_use:
        #     with self.lock:
        #         self.debug('Used')
        #         self.icomm.drain_messages()
        #         self.icomm.close()
        return flag

    def set_close_state(self, state):
        r"""Set the close state if its not already set."""
        out = False
        with self.lock:
            if not self.close_state:
                self.debug("Setting close state to %s", state)
                self.close_state = state
                out = True
        return out

    def wait_close_state(self, state, timeout=None):
        r"""Set the close state after waiting for specified time for the
        close state to be set by another method.

        Args:
            state (str): Close state that should be set after timeout.
            timeout (float, optional): Time that should be waited before
                setting the timeout. Defaults to self.timeout.

        """
        T = self.start_timeout(timeout)
        while (not T.is_out):  # pragma: debug
            with self.lock:
                if self.close_state:
                    break
            self.sleep(2 * self.sleeptime)
        self.stop_timeout()
        self.set_close_state(state)

    def run_loop(self):
        r"""Run the driver. Continue looping over messages until there are not
        any left or the communication channel is closed.
        """
        self.state = 'in loop'
        if not self.is_valid:
            self.debug("Breaking loop")
            self.set_close_state('invalid')
            # self.info("%s: breaking loop, input=%s, output=%s", self.name,
            #           self.icomm.is_open, self.ocomm.is_open)
            self.set_break_flag()
            return
        # Receive a message
        self.state = 'receiving'
        msg = self.recv_message()
        if msg is False:
            self.debug('No more messages')
            self.set_break_flag()
            self.set_close_state('receiving')
            return
        if ((isinstance(msg, type(self.icomm.serializer.empty_msg)) and
             (msg == self.icomm.serializer.empty_msg))):
            self.state = 'waiting'
            self.verbose_debug(':run: Waiting for next message.')
            self.sleep()
            return
        self.nrecv += 1
        self.state = 'received'
        if isinstance(msg, backwards.bytes_type):
            self.debug('Received message that is %d bytes from %s.',
                       len(msg), self.icomm.address)
        elif isinstance(msg, np.ndarray):
            self.debug('Received array with shape %s and data type %s from %s',
                       msg.shape, msg.dtype, self.icomm.address)
        else:
            self.debug('Received message of type %s from %s',
                       type(msg), self.icomm.address)
        # Process message
        self.state = 'processing'
        msg = self.on_message(msg)
        if msg is False:  # pragma: debug
            self.error('Could not process message.')
            self.set_break_flag()
            self.set_close_state('processing')
            return
        elif ((isinstance(msg, type(self.ocomm.serializer.empty_msg)) and
               (msg == self.ocomm.serializer.empty_msg))):
            self.debug('Message skipped.')
            self.nskip += 1
            return
        self.nproc += 1
        self.state = 'processed'
        self.debug('Processed message.')
        # Send a message
        self.state = 'sending'
        ret = self.send_message(msg)
        if ret is False:
            self.error('Could not send message.')
            self.set_break_flag()
            self.set_close_state('sending')
            return
        self.nsent += 1
        self.state = 'sent'
        self.debug('Sent message to %s.', self.ocomm.address)
