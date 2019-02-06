"""Module for funneling messages from one comm to another."""
import os
import numpy as np
import threading
from yggdrasil import backwards
from yggdrasil.communication import new_comm, get_comm_class
from yggdrasil.drivers.Driver import Driver
from yggdrasil.schema import get_schema


def _translate_list2element(arr):
    if isinstance(arr, (list, tuple)):
        arr = arr[0]
    return arr


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

    _connection_type = 'default'
    _icomm_type = 'DefaultComm'
    _ocomm_type = 'DefaultComm'
    _direction = 'any'
    _schema_type = 'connection'
    _schema_required = ['inputs', 'outputs']
    _schema_properties = {
        'inputs': {'type': 'array', 'minItems': 1,
                   'items': {'anyOf': [{'$ref': '#/definitions/comm'},
                                       {'$ref': '#/definitions/file'}]}},
        'outputs': {'type': 'array', 'minItems': 1,
                    'items': {'anyOf': [{'$ref': '#/definitions/comm'},
                                        {'$ref': '#/definitions/file'}]}},
        'translator': {'type': 'array', 'items': {'type': 'function'}},
        'onexit': {'type': 'string'}}

    @property
    def _is_input(self):
        r"""bool: True if the connection is providing input to a model."""
        return (self._direction == 'input')

    @property
    def _is_output(self):
        r"""bool: True if the connection is retreiving output from a model."""
        return (self._direction == 'output')

    def __init__(self, name, translator=None, single_use=False, onexit=None, **kwargs):
        super(ConnectionDriver, self).__init__(name, **kwargs)
        # Translator
        if translator is None:
            translator = []
        elif not isinstance(translator, list):
            translator = [translator]
        self.translator = []
        for t in translator:
            if not hasattr(t, '__call__'):
                raise ValueError("Translator %s not callable." % t)
            self.translator.append(t)
        if (onexit is not None) and (not hasattr(self, onexit)):
            raise ValueError("onexit '%s' is not a class method." % onexit)
        self.onexit = onexit
        # Attributes
        self._eof_sent = False
        self.single_use = single_use
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
        # self.debug('    env: %s', str(self.env))
        self.debug(('\n' + 80 * '=' + '\n'
                    + 'class = %s\n'
                    + '    input: name = %s, address = %s\n'
                    + '    output: name = %s, address = %s\n'
                    + (80 * '=')), self.__class__,
                   self.icomm.name, self.icomm.address,
                   self.ocomm.name, self.ocomm.address)

    def _init_single_comm(self, name, io, comm_kws, **kwargs):
        r"""Parse keyword arguments for input/output comm."""
        self.debug("Creating %s comm", io)
        s = get_schema()
        if comm_kws is None:
            comm_kws = dict()
        if io == 'input':
            direction = 'recv'
            comm_type = self._icomm_type
            touches_model = self._is_output
            attr_comm = 'icomm'
            comm_kws['close_on_eof_recv'] = False
        else:
            direction = 'send'
            comm_type = self._ocomm_type
            touches_model = self._is_input
            attr_comm = 'ocomm'
        comm_kws['direction'] = direction
        comm_kws['dont_open'] = True
        comm_kws['reverse_names'] = True
        comm_kws.setdefault('comm', {'comm': comm_type})
        assert(name == self.name)
        comm_kws.setdefault('name', name)
        if not isinstance(comm_kws['comm'], list):
            comm_kws['comm'] = [comm_kws['comm']]
        for i, x in enumerate(comm_kws['comm']):
            if x is None:
                comm_kws['comm'][i] = dict()
            elif not isinstance(x, dict):
                comm_kws['comm'][i] = dict(comm=x)
            comm_kws['comm'][i].setdefault('comm', comm_type)
        any_files = False
        all_files = True
        if not touches_model:
            comm_kws['no_suffix'] = True
            ikws = []
            for x in comm_kws['comm']:
                if get_comm_class(x['comm']).is_file:
                    any_files = True
                    ikws += s['file'].get_subtype_properties(x['comm'])
                else:
                    all_files = False
                    ikws += s['comm'].get_subtype_properties(x['comm'])
            ikws = list(set(ikws))
            for k in ikws:
                if (k not in comm_kws) and (k in kwargs):
                    comm_kws[k] = kwargs.pop(k)
            if ('comm_env' in kwargs) and ('comm_env' not in comm_kws):
                comm_kws['env'] = kwargs.pop('comm_env')
        if any_files and (io == 'input'):
            kwargs.setdefault('timeout_send_1st', 60)
        self.debug('%s comm_kws:\n%s', attr_comm, self.pprint(comm_kws, 1))
        setattr(self, attr_comm, new_comm(comm_kws.pop('name'), **comm_kws))
        setattr(self, '%s_kws' % attr_comm, comm_kws)
        if touches_model:
            self.env.update(getattr(self, attr_comm).opp_comms)
        elif not all_files:
            self.comm_env.update(getattr(self, attr_comm).opp_comms)
        return kwargs

    def _init_comms(self, name, icomm_kws=None, ocomm_kws=None, **kwargs):
        r"""Parse keyword arguments for input/output comms."""
        kwargs = self._init_single_comm(name, 'input', icomm_kws, **kwargs)
        try:
            kwargs = self._init_single_comm(name, 'output', ocomm_kws, **kwargs)
        except BaseException:
            self.icomm.close()
            raise
        # Apply keywords dependent on comms
        self.timeout_send_1st = kwargs.pop('timeout_send_1st', self.timeout)
        self.debug('Final env:\n%s', self.pprint(self.env, 1))
        
    def wait_for_route(self, timeout=None):
        r"""Wait until messages have been routed."""
        T = self.start_timeout(timeout)
        while ((not T.is_out)
               and (self.nrecv != (self.nsent + self.nskip))):  # pragma: debug
            self.sleep()
        self.stop_timeout()
        return (self.nrecv == (self.nsent + self.nskip))

    @property
    def is_valid(self):
        r"""bool: Returns True if the connection is open and the parent class
        is valid."""
        with self.lock:
            return (super(ConnectionDriver, self).is_valid
                    and self.is_comm_open and not (self.single_use and self._used))

    @property
    def is_comm_open(self):
        r"""bool: Returns True if both communicators are open."""
        with self.lock:
            return (self.icomm.is_open and self.ocomm.is_open
                    and not self._comm_closed)

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
                elif ((self.icomm.n_msg_recv_drain == 0)
                      and self.icomm.is_confirmed_recv):
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
                elif ((self.ocomm.n_msg_send_drain == 0)
                      and self.ocomm.is_confirmed_send):
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
        if (self.ocomm._send_serializer) and self.icomm.serializer._initialized:
            self.update_serializer(msg)
        for t in self.translator:
            msg = t(msg)
        return msg

    def update_serializer(self, msg):
        r"""Update the serializer for the output comm based on input."""
        sinfo = self.icomm.serializer.typedef
        sinfo.update(self.icomm.serializer.serializer_info)
        sinfo.pop('seritype', None)
        self.debug('Before update:\n'
                   + '  icomm:\n    sinfo:\n%s\n    typedef:\n%s\n'
                   + '  ocomm:\n    sinfo:\n%s\n    typedef:\n%s',
                   self.pprint(self.icomm.serializer.serializer_info, 2),
                   self.pprint(self.icomm.serializer.typedef, 2),
                   self.pprint(self.ocomm.serializer.serializer_info, 2),
                   self.pprint(self.ocomm.serializer.typedef, 2))
        self.ocomm.serializer.initialize_serializer(sinfo)
        self.ocomm.serializer.update_serializer(skip_type=True,
                                                **self.icomm._last_header)
        if (((self.icomm.serializer.typedef['type'] == 'array')
             and (self.ocomm.serializer.typedef['type'] != 'array')
             and (len(self.icomm.serializer.typedef['items']) == 1))):
            self.translator.insert(0, _translate_list2element)
        # inter_model = False
        # if self.icomm.is_file:
        #     # Remove the file information and only pass the type definition
        #     typedef_in = self.icomm.serializer.typedef
        #     sinfo = self.icomm.serializer.typedef
        #     sinfo.pop('seritype', None)
        # elif self.ocomm.is_file:
        #     # Maintain the default serializer type for the file
        #     sinfo = self.icomm.serializer.serializer_info
        #     sinfo.pop('seritype')
        #     sinfo.update(self.ocomm.serializer.serializer_info)
        #     sinfo.update(self.icomm.serializer.typedef)
        # else:
        #     # Copy the serializer and prevent the type from being overwritten
        #     # TODO: icomm is probably initialized so the serializer info
        #     # from the output comm won't be used.
        #     sinfo = self.ocomm.serializer.serializer_info
        #     sinfo.pop('seritype', None)
        #     self.ocomm.serializer = self.icomm.serializer
        #     inter_model = True
        # if (not inter_model) and self.ocomm.serializer._initialized:  # pragma: debug
        #     self.ocomm.serializer.update_serializer(**sinfo)
        # else:
        #     self.ocomm.serializer.initialize_serializer(sinfo)
        self.debug('After update:\n'
                   + '  icomm:\n    sinfo:\n%s\n    typedef:\n%s\n'
                   + '  ocomm:\n    sinfo:\n%s\n    typedef:\n%s',
                   self.pprint(self.icomm.serializer.serializer_info, 2),
                   self.pprint(self.icomm.serializer.typedef, 2),
                   self.pprint(self.ocomm.serializer.serializer_info, 2),
                   self.pprint(self.ocomm.serializer.typedef, 2))

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
        while ((not T.is_out) and (not flag)
               and self.ocomm.is_open):  # pragma: debug
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
        if self.icomm.is_empty_recv(msg):
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
        elif self.ocomm.is_empty_send(msg):
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
