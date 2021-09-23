import uuid
from yggdrasil import multitasking
from yggdrasil.tools import ProxyObject
from yggdrasil.components import ComponentBaseUnregistered
from yggdrasil.communication import (
    CommBase, TemporaryCommunicationError)


FLAG_FAILURE = 0
FLAG_SUCCESS = 1
FLAG_TRYAGAIN = 2


class AsyncComm(ProxyObject, ComponentBaseUnregistered):
    r"""Class for handling asynchronous I/O.

    Args:
        name (str): The name of the message queue.
        async_recv_method (str, optional): The method that should be used
            to receive message into the backlog. Defaults to 'recv'.
        async_send_method (str, optional): The method that should be used
            to send message in the backlog. Defaults to 'send_message'.
        async_recv_kwargs (dict, optional): Keyword arguments to pass to calls
            receiving messages into the backlog. Defaults to {}.
        async_send_method (dict, optional): Keyword arguments to pass to calls
            sending message from the backlog. Defaults to {}.
        **kwargs: Additional keyword arguments are passed to CommBase.
        
    Attributes:
        backlog_ready (multitasking.Event): Event set when there is a
            message in the recv backlog.
        
    """

    __slots__ = ['_backlog_buffer', '_backlog_thread',
                 'backlog_ready', '_used_direct', 'close_on_eof_recv',
                 '_backlog_received_eof', '_used', '_closed',
                 'async_recv_method', 'async_send_method',
                 'async_recv_kwargs', 'async_send_kwargs',
                 '_error_registry', 'daemon']
    __overrides__ = ['_input_args', '_input_kwargs']
    _disconnect_attr = ['backlog_ready', '_backlog_thread', '_wrapped']
    _async_kws = ['async_recv_method', 'async_send_method',
                  'async_recv_kwargs', 'async_send_kwargs', 'daemon']

    def __init__(self, wrapped, daemon=False,
                 async_recv_method='recv', async_send_method='send_message',
                 async_recv_kwargs=None, async_send_kwargs=None):
        self._backlog_buffer = []
        self._backlog_thread = None
        self.backlog_ready = multitasking.Event()
        self._used_direct = False
        self.close_on_eof_recv = wrapped.close_on_eof_recv
        self._used = False
        self._closed = False
        self._backlog_received_eof = False
        self._error_registry = {}
        self.daemon = daemon
        self.async_recv_method = async_recv_method
        self.async_send_method = async_send_method
        if async_recv_kwargs is None:
            async_recv_kwargs = {}
        if async_send_kwargs is None:
            async_send_kwargs = {}
        self.async_recv_kwargs = async_recv_kwargs
        self.async_send_kwargs = async_send_kwargs
        wrapped.close_on_eof_recv = False
        wrapped.is_async = True
        super(AsyncComm, self).__init__(wrapped)
        # Open backlog to match
        if self._wrapped.is_open:
            self.open()
        if self._wrapped.is_interface:  # pragma: debug
            # atexit.register(self.atexit)
            raise RuntimeError("Use of async comm inside model is untested")

    def __reduce__(self):
        rv = list(super(AsyncComm, self).__reduce__())
        (wrapped, ) = rv[1]
        wrapped.close_on_eof_recv = self.close_on_eof_recv
        rv[1] = (wrapped, )
        return tuple(rv)

    def precheck(self, *args, **kwargs):
        CommBase.CommBase.precheck(self, *args, **kwargs)

    def printStatus(self, *args, **kwargs):
        r"""Print status of the communicator."""
        lines = ['%-15s: %s' % ('open (backlog)', self.is_open_backlog),
                 '%-15s: %s' % ('close called (backlog)', self._closed)]
        if self.direction == 'send':
            lines.append(
                '%-15s: %s' % ('nsent (backlog)', self.n_msg_backlog_send))
        else:
            lines.append(
                '%-15s: %s' % ('nrecv (backlog)', self.n_msg_backlog_recv))
        kwargs.setdefault('extra_lines_after', [])
        kwargs['extra_lines_after'] += lines
        return self._wrapped.printStatus(*args, **kwargs)
        
    @property
    def backlog_thread(self):
        r"""tools.YggTask: Task that will handle sinding or receiving
        backlogged messages."""
        if self._backlog_thread is None:
            if self.direction == 'send':
                self._backlog_thread = CommBase.CommTaskLoop(
                    self, target=self.run_backlog_send,
                    daemon=self.daemon, suffix='SendBacklog')
            else:
                self._backlog_thread = CommBase.CommTaskLoop(
                    self, target=self.run_backlog_recv,
                    daemon=self.daemon, suffix='RecvBacklog')
        return self._backlog_thread

    @property
    def errors(self):
        r"""list: Errors raised by the wrapped comm or async thread."""
        out = self._wrapped.errors
        if self._backlog_thread:
            out += self._backlog_thread.errors
            self._backlog_thread.errors = []
        return out

    def atexit(self):  # pragma: debug
        r"""Close operations."""
        if (self.direction == 'send') and self.is_open_backlog:
            self.linger()

    def open(self):
        r"""Open the connection by connecting to the queue."""
        self._wrapped.open()
        self._wrapped.suppress_special_debug = True
        if self._wrapped.is_open and (not self.is_open_backlog):
            self.backlog_thread.start()

    def close(self, linger=False):
        r"""Close the connection.

        Args:
            linger (bool, optional): If True, drain messages before closing the
                comm. Defaults to False.

        """
        with self._closing_thread.lock:
            self._wrapped.close(linger=linger)
            self._close_backlog(wait=linger)
        with self.backlog_thread.lock:
            self._closed = True
        # Requeue messages for other servers
        if ((self.is_server and (self.model_copies > 1)
             and self._backlog_buffer)):  # pragma: debug
            # client_kws = self.opp_comm_kwargs
            # client_kws.update(use_async=False)
            # client = get_comm(self.name + '_client', **client_kws)
            # for msg in self._backlog_buffer:
            #     self.info("Resending: %s", msg)
            #     client.send(msg[0])
            # client.close()
            raise RuntimeError("Returning backlogged messages to the server "
                               "is untested.")

    def _close_backlog(self, wait=False):
        r"""Close the backlog thread."""
        self.debug('')
        if self._backlog_thread is not None:
            self.backlog_thread.set_break_flag()
        self.backlog_ready.set()
        if wait and (self._backlog_thread is not None):  # pragma: intermittent
            self.backlog_thread.wait(key=str(uuid.uuid4()))
        if hasattr(self._wrapped, '_close_backlog'):
            self._wrapped._close_backlog(wait=wait)

    @property
    def is_open(self):
        r"""bool: True if the backlog is open."""
        if self.direction == 'send':
            return self._wrapped.is_open and self.is_open_backlog
        else:
            return ((self.is_open_backlog or (self.n_msg_backlog > 0))
                    and (not self._closed))

    @property
    def is_open_direct(self):
        r"""bool: True if the direct comm is not None."""
        return self._wrapped.is_open

    @property
    def is_open_backlog(self):
        r"""bool: True if the backlog thread is running."""
        return ((self._backlog_thread is not None)
                and (not self.backlog_thread.was_break)
                and (self.backlog_thread.is_alive()))

    @property
    def is_closed(self):
        r"""bool: True if the connection is closed."""
        return (not self.is_open)

    @property
    def n_msg(self):
        r"""int: The number of messages in the connection."""
        if self.direction == 'recv':
            return self.n_msg_recv
        else:
            return self.n_msg_send

    @property
    def n_msg_recv(self):
        r"""int: Number of messages in the receive backlog."""
        return self.n_msg_backlog_recv

    @property
    def n_msg_send(self):
        r"""int: Number of messages in the send backlog."""
        return self.n_msg_backlog_send

    @property
    def n_msg_direct_recv(self):
        r"""int: Number of messages currently being routed in recv."""
        return self._wrapped.n_msg_recv

    @property
    def n_msg_direct_send(self):
        r"""int: Number of messages currently being routed in send."""
        return self._wrapped.n_msg_send

    @property
    def n_msg_direct(self):
        r"""int: Number of messages currently being routed."""
        if self.direction == 'send':
            return self.n_msg_direct_send
        else:
            return self.n_msg_direct_recv

    @property
    def n_msg_backlog_recv(self):
        r"""int: Number of messages in the receive backlog."""
        if self.direction == 'recv':
            return self.n_msg_backlog
        return 0  # pragma: debug

    @property
    def n_msg_backlog_send(self):
        r"""int: Number of messages in the send backlog."""
        if self.direction == 'send':
            return self.n_msg_backlog
        return 0  # pragma: debug

    @property
    def n_msg_backlog(self):
        r"""int: Number of messages in the backlog."""
        if (self.direction == 'recv') or self.is_open_backlog:
            return len(self.backlog_buffer)
        return 0

    @property
    def n_msg_recv_drain(self):
        r"""int: Number of messages in the receive backlog and direct comm."""
        return self.n_msg_direct_recv + self.n_msg_backlog_recv

    @property
    def n_msg_send_drain(self):
        r"""int: Number of messages in the send backlog and direct comm."""
        return self.n_msg_direct_send + self.n_msg_backlog_send

    @property
    def is_confirmed_send(self):
        r"""bool: True if all sent messages have been confirmed."""
        if not self._wrapped.is_confirmed_send:
            return False
        return (self.n_msg_send == 0)
        
    @property
    def backlog_buffer(self):
        r"""list: Messages that have been received."""
        with self.backlog_thread.lock:
            return self._backlog_buffer

    def add_backlog(self, payload):
        r"""Add a message to the backlog of messages.

        Args:
            payload (tuple): Arguments and keyword argumetns for send
                or data from receive.

        """
        with self.backlog_thread.lock:
            self.debug("Added message to %s backlog.",
                       self.direction)
            if not self._closed:
                self._backlog_buffer.append(payload)
                self.backlog_ready.set()

    def pop_backlog(self):
        r"""Pop a message from the front of the backlog.

        Returns:
            tuple: First backlogged send arguments/keyword arguments
                or received data.

        """
        with self.backlog_thread.lock:
            out = self._backlog_buffer.pop(0)
            self.debug("Removed message from backlog.")
            if len(self._backlog_buffer) == 0:
                self.backlog_ready.clear()
        return out

    def run_backlog_send(self):
        r"""Continue trying to send buffered messages."""
        if not self.send_backlog():  # pragma: debug
            self.debug("Stopping because send_backlog failed")
            self._close_backlog()
            return
        self.periodic_debug('run_backlog_send', period=1000)(
            "Sleeping (is_confirmed_send=%s, n_msg_send=%d)",
            str(self.is_confirmed_send), self.n_msg_backlog_send)
        self.sleep()

    def run_backlog_recv(self):
        r"""Continue buffering received messages."""
        if self.backlog_thread.main_terminated:  # pragma: debug
            self.debug("Main thread terminated")
            self.close()
            return
        if not self.recv_backlog():
            self.debug("Failure to receive message into backlog.")
            self._close_backlog()
            return
        self.periodic_debug('run_backlog_recv', period=1000)(
            "Sleeping (is_confirmed_recv=%s)",
            str(self.is_confirmed_recv))
        self.sleep()

    def send_direct(self, *args, **kwargs):
        r"""Send a message directly to the underlying comm."""
        self.periodic_debug("send_direct", period=1000)(
            "Sending message to %s", self.address)
        self.suppress_special_debug = True
        kwargs.update(self.async_send_kwargs)
        try:
            kwargs.setdefault('timeout', 0)
            if getattr(self._wrapped, self.async_send_method)(*args, **kwargs):
                async_flag = FLAG_SUCCESS
                self._used_direct = True
            else:
                async_flag = FLAG_FAILURE
            self._error_registry = {}
        except TemporaryCommunicationError:
            async_flag = FLAG_TRYAGAIN
        self.suppress_special_debug = False
        return async_flag

    def recv_direct(self):
        r"""Receive a message directly from the underlying comm."""
        self.periodic_debug("recv_direct", period=1000)(
            "Receiving message from %s", self.address)
        self.suppress_special_debug = True
        msg = None
        kwargs = self.async_recv_kwargs
        try:
            kwargs.setdefault('timeout', 0)
            if self.async_recv_method != 'recv_message':
                kwargs['return_message_object'] = True
            msg = getattr(self._wrapped, self.async_recv_method)(**kwargs)
            if msg.flag in [CommBase.FLAG_EMPTY, CommBase.FLAG_SKIP]:
                async_flag = FLAG_TRYAGAIN  # pragma: debug
            elif msg.flag in [CommBase.FLAG_SUCCESS, CommBase.FLAG_EOF]:
                async_flag = FLAG_SUCCESS
                self._used_direct = True
                if msg.flag == CommBase.FLAG_EOF:
                    self._backlog_received_eof = True
            elif msg.flag == CommBase.FLAG_FAILURE:
                async_flag = FLAG_FAILURE
            else:  # pragma: debug
                raise Exception("Unsupported flag: %s" % msg.flag)
            self._error_registry = {}
        except TemporaryCommunicationError:
            async_flag = FLAG_TRYAGAIN
        self.suppress_special_debug = False
        return async_flag, msg

    def send_backlog(self):
        r"""Send a message from the send backlog to the queue."""
        if len(self.backlog_buffer) == 0:
            flag = True
        else:
            iargs, ikwargs = self.backlog_buffer[0]
            async_flag = self.send_direct(*iargs, **ikwargs)
            flag = bool(async_flag)
            if async_flag == FLAG_SUCCESS:
                self.pop_backlog()
        self.confirm_send()
        return flag

    def recv_backlog(self):
        r"""Check for any messages in the queue and add them to the recv
        backlog."""
        if not self.is_open_direct:
            flag = False
        elif self._backlog_received_eof and self.close_on_eof_recv:
            # Don't keep receiving, but don't close so that this thread
            # can continue confirmation until the EOF is actually received
            flag = True
        else:
            async_flag, msg = self.recv_direct()
            flag = bool(async_flag)
            if async_flag == FLAG_SUCCESS:
                self.add_backlog(msg)
        self.confirm_recv()
        return flag

    def send_message(self, msg, **kwargs):
        r"""Send a message encapsulated in a CommMessage object.

        Args:
            msg (CommMessage): Message to be sent.
            **kwargs: Additional keyword arguments are passed to _safe_send.

        Returns:
            bool: Success or failure of send.
        
        """
        # This is required so that call to send_message for work comms
        # in CommBase.send_message will put the messages in the backlog
        kwargs['dont_prepare'] = True
        return self.send(msg, **kwargs)
        
    def send(self, *args, dont_prepare=False, **kwargs):
        r"""Send a message to the backlog.

        Args:
            *args: All arguments are assumed to be part of the message.
            **kwargs: All keywords arguments are passed to comm _send method.

        Returns:
            bool: Success or failure of sending the message.

        """
        self.precheck('send')
        kws_prepare = {k: kwargs.pop(k) for k in self._prepare_message_kws
                       if k in kwargs}
        if not self.is_open_direct:  # pragma: debug
            return False
        if dont_prepare:
            assert((len(args) == 1) and isinstance(args[0], CommBase.CommMessage))
            msg = args[0]
        else:
            msg = self._wrapped.prepare_message(*args, **kws_prepare)
        if not self.backlog_ready.is_set():
            async_flag = self.send_direct(msg, **kwargs)
            if async_flag != FLAG_TRYAGAIN:
                return bool(async_flag)
        self.add_backlog(((msg, ), kwargs))
        self._used = True
        return True

    def send_eof(self, *args, **kwargs):
        r"""Send the EOF message as a short message.
        
        Args:
            *args: All arguments are passed to comm send.
            **kwargs: All keywords arguments are passed to comm send.

        Returns:
            bool: Success or failure of send.

        """
        return self.send(self.eof_msg, *args, **kwargs)

    def recv_message(self, timeout=None, **kwargs):
        r"""Receive a message.

        Args:
            *args: Arguments are passed to the response comm's recv_message method.
            **kwargs: Keyword arguments are passed to the response comm's recv_message
                method.

        Returns:
            CommMessage: Received message.

        """
        # Sleep until there is a message
        if timeout is None:
            timeout = kwargs.get('timeout', self.recv_timeout)
        T = self.start_timeout(timeout, key_suffix='.recv:backlog')
        while (not T.is_out) and (not self.backlog_ready.is_set()):
            self.backlog_ready.wait(self.sleeptime)
        self.stop_timeout(key_suffix='.recv:backlog')
        # Handle absence of messages
        if self.n_msg_backlog == 0:
            self.verbose_debug("No messages waiting.")
            if self.is_closed:
                self.debug(("No messages waiting and comm closed."
                            "%s, %s, %s")
                           % (self.backlog_thread is not None,
                              not self.backlog_thread.was_break,
                              self.backlog_thread.is_alive()))
                self.printStatus(level='debug')
                if self.backlog_thread.was_break:
                    self.debug("Break stack:\n%s",
                               self.backlog_thread.break_stack)
                out = CommBase.CommMessage(flag=CommBase.FLAG_FAILURE)
            else:
                out = CommBase.CommMessage(flag=CommBase.FLAG_EMPTY,
                                           args=self.empty_obj_recv)
        # Return backlogged message
        else:
            self.debug('Returning backlogged received message')
            out = self.pop_backlog()
        return out
        
    def finalize_message(self, msg, **kwargs):
        r"""Perform actions to decipher a message.

        Args:
            msg (CommMessage): Initial message object to be finalized.
            **kwargs: Keyword arguments are passed to the request comm's
                finalize_message method.

        Returns:
            CommMessage: Deserialized and annotated message.

        """
        orig_flag = msg.flag
        if (msg.flag == CommBase.FLAG_EOF) and self.close_on_eof_recv:
            self.close()
            msg.flag = CommBase.FLAG_FAILURE
        if orig_flag not in [CommBase.FLAG_FAILURE, CommBase.FLAG_EMPTY]:
            self._used = True
        if self.async_recv_method != 'recv_message':
            msg.finalized = False
            kwargs['skip_processing'] = True
        return self._wrapped.finalize_message(msg, **kwargs)
        
    def recv(self, timeout=None, return_message_object=False, dont_finalize=False,
             **kwargs):
        r"""Receive a message.

        Args:
            *args: All arguments are passed to comm _recv method.
            return_message_object (bool, optional): If True, the full wrapped
                CommMessage message object is returned instead of the tuple.
                Defaults to False.
            dont_finalize (bool, optional): If True, finalize_message will not
                be called even if async_recv_method is 'recv_message'. Defaults
                to False.
            **kwargs: All keywords arguments are passed to comm _recv method.

        Returns:
            tuple (bool, obj): Success or failure of receive and received
                message.

        """
        self.precheck('recv')
        out = self.recv_message(timeout=timeout, **kwargs)
        if not dont_finalize:
            kws_finalize = {k: kwargs.pop(k) for k in self._finalize_message_kws
                            if k in kwargs}
            out = self.finalize_message(out, **kws_finalize)
        if not return_message_object:
            out = (bool(out.flag), out.args)
        return out

    def purge(self):
        r"""Purge all messages from the comm."""
        self._wrapped.purge()
        with self.backlog_thread.lock:
            self.backlog_ready.clear()
            self._backlog_buffer = []

    # ALIASES
    def send_nolimit(self, *args, **kwargs):
        r"""Alias for send_nolimit on wrapped comm."""
        return CommBase.CommBase.send_nolimit(self, *args, **kwargs)

    def recv_nolimit(self, *args, **kwargs):
        r"""Alias for recv_nolimit on wrapped comm."""
        return CommBase.CommBase.recv_nolimit(self, *args, **kwargs)

    def send_array(self, *args, **kwargs):
        r"""Alias for send_array on wrapped comm."""
        return CommBase.CommBase.send_array(self, *args, **kwargs)

    def recv_array(self, *args, **kwargs):
        r"""Alias for recv_array on wrapped comm."""
        return CommBase.CommBase.recv_array(self, *args, **kwargs)

    def send_dict(self, *args, **kwargs):
        r"""Alias for send_dict on wrapped comm."""
        return CommBase.CommBase.send_dict(self, *args, **kwargs)

    def recv_dict(self, *args, **kwargs):
        r"""Alias for recv_dict on wrapped comm."""
        return CommBase.CommBase.recv_dict(self, *args, **kwargs)
