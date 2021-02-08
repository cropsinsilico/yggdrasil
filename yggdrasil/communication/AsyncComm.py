import uuid
import atexit
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
        **kwargs: Additional keyword arguments are passed to CommBase.
        
    Attributes:
        backlog_ready (multitasking.Event): Event set when there is a
            message in the recv backlog.
        
    """

    __slots__ = ['_backlog_buffer', '_backlog_thread',
                 'backlog_ready', '_used_direct', 'close_on_eof_recv',
                 '_used', '_closed']
    __overrides__ = ['_input_args', '_input_kwargs']
    _disconnect_attr = ['backlog_ready', '_backlog_thread', '_wrapped']

    def __init__(self, wrapped):
        self._backlog_buffer = []
        self._backlog_thread = None
        self.backlog_ready = multitasking.Event()
        self._used_direct = False
        self.close_on_eof_recv = wrapped.close_on_eof_recv
        self._used = False
        self._closed = False
        wrapped.close_on_eof_recv = False
        wrapped.is_async = True
        super(AsyncComm, self).__init__(wrapped)
        # Open backlog to match
        if self._wrapped.is_open:
            self.open()
        if self._wrapped.is_interface:
            atexit.register(self.atexit)

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
        self._wrapped.printStatus(*args, **kwargs)
        
    @property
    def backlog_thread(self):
        r"""tools.YggTask: Task that will handle sinding or receiving
        backlogged messages."""
        if self._backlog_thread is None:
            if self.direction == 'send':
                self._backlog_thread = CommBase.CommTaskLoop(
                    self, target=self.run_backlog_send, suffix='SendBacklog')
            else:
                self._backlog_thread = CommBase.CommTaskLoop(
                    self, target=self.run_backlog_recv, suffix='RecvBacklog')
        return self._backlog_thread

    def atexit(self):
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

    def _close_backlog(self, wait=False):
        r"""Close the backlog thread."""
        self.debug('')
        if self._backlog_thread is not None:
            self.backlog_thread.set_break_flag()
        self.backlog_ready.set()
        if wait and (self._backlog_thread is not None):
            self.backlog_thread.wait(key=str(uuid.uuid4()))
        if hasattr(self._wrapped, '_close_backlog'):
            self._wrapped._close_backlog(wait=wait)

    def stop_backlog(self):
        r"""Stop the asynchronous backlog, turning this into a direct comm."""
        self._close_backlog(wait=True)

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
        return 0

    @property
    def n_msg_backlog_send(self):
        r"""int: Number of messages in the send backlog."""
        if self.direction == 'send':
            return self.n_msg_backlog
        return 0

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
        try:
            kwargs.setdefault('timeout', 0)
            if self._wrapped.send(*args, **kwargs):
                async_flag = FLAG_SUCCESS
                self._used_direct = True
            else:
                async_flag = FLAG_FAILURE
        except TemporaryCommunicationError:
            async_flag = FLAG_TRYAGAIN
        self.suppress_special_debug = False
        return async_flag

    def recv_direct(self, **kwargs):
        r"""Receive a message directly from the underlying comm."""
        self.periodic_debug("recv_direct", period=1000)(
            "Receiving message from %s", self.address)
        self.suppress_special_debug = True
        data = None
        header = None
        try:
            kwargs.setdefault('timeout', 0)
            kwargs['return_header'] = True
            flag, data, header = self._wrapped.recv(**kwargs)
            if flag:
                if self._wrapped.is_empty_recv(data):
                    async_flag = FLAG_TRYAGAIN
                else:
                    async_flag = FLAG_SUCCESS
                    self._used_direct = True
            else:
                if self.is_eof(data):
                    async_flag = FLAG_SUCCESS
                else:
                    async_flag = FLAG_FAILURE
        except TemporaryCommunicationError:
            async_flag = FLAG_TRYAGAIN
        self.suppress_special_debug = False
        return async_flag, data, header

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
        else:
            async_flag, data, header = self.recv_direct()
            flag = bool(async_flag)
            if async_flag == FLAG_SUCCESS:
                self.add_backlog((data, header))
        self.confirm_recv()
        return flag

    def send(self, *args, **kwargs):
        r"""Send a message to the backlog.

        Args:
            *args: All arguments are assumed to be part of the message.
            **kwargs: All keywords arguments are passed to comm _send method.

        Returns:
            bool: Success or failure of sending the message.

        """
        self.precheck('send')
        if not self.is_open_direct:  # pragma: debug
            return False
        if not self.backlog_ready.is_set():
            async_flag = self.send_direct(*args, **kwargs)
            if async_flag != FLAG_TRYAGAIN:
                return bool(async_flag)
        self.add_backlog((args, kwargs))
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

    def recv(self, timeout=None, return_header=False, **kwargs):
        r"""Receive a message.

        Args:
            *args: All arguments are passed to comm _recv method.
            **kwargs: All keywords arguments are passed to comm _recv method.

        Returns:
            tuple (bool, obj): Success or failure of receive and received
                message.

        """
        self.precheck('recv')
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
                self.info(("No messages waiting and comm closed."
                           "%s, %s, %s")
                          % (self.backlog_thread is not None,
                             not self.backlog_thread.was_break,
                             self.backlog_thread.is_alive()))
                self.printStatus()
                if self.backlog_thread.was_break:
                    self.info("Break stack:\n%s",
                              self.backlog_thread.break_stack)
                out = (False, None, None)
            else:
                out = (True, self.empty_obj_recv, None)
        # Return backlogged message
        else:
            self.debug('Returning backlogged received message')
            msg, header = self.pop_backlog()
            flag = True
            if self.is_eof(msg) and self.close_on_eof_recv:
                flag = False
                self.close()
            self._used = True
            out = (flag, msg, header)
        if not return_header:
            out = (out[0], out[1])
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
