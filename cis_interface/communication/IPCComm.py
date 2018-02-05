import sys
from logging import warn
import threading
from subprocess import Popen, PIPE
from cis_interface import platform
from cis_interface.tools import get_CIS_MSG_MAX
from cis_interface.tools import _ipc_installed as _ipc_installed0
from cis_interface.communication import CommBase
try:
    import sysv_ipc
    _ipc_installed = _ipc_installed0
except ImportError:
    warn("Could not import sysv_ipc. " +
         "IPC support will be disabled.")
    sysv_ipc = None
    _ipc_installed = False

_registered_queues = {}


def get_queue(qid=None):
    r"""Create or return a sysv_ipc.MessageQueue and register it.

    Args:
        qid (int, optional): If provided, ID for existing queue that should be
           returned. Defaults to None and a new queue is returned.

    Returns:
        :class:`sysv_ipc.MessageQueue`: Message queue.

    """
    if _ipc_installed:
        global _registered_queues
        kwargs = dict(max_message_size=get_CIS_MSG_MAX())
        if qid is None:
            kwargs['flags'] = sysv_ipc.IPC_CREX
        mq = sysv_ipc.MessageQueue(qid, **kwargs)
        key = str(mq.key)
        if key not in _registered_queues:
            _registered_queues[key] = mq
        return mq
    else:
        warn("IPC not installed. Queue cannot be returned.")
        return None


def remove_queue(mq):
    r"""Remove a sysv_ipc.MessageQueue and unregister it.

    Args:
        mq (:class:`sysv_ipc.MessageQueue`) Message queue.
    
    Raises:
        KeyError: If the provided queue is not registered.

    """
    global _registered_queues
    key = str(mq.key)
    if key not in _registered_queues:
        raise KeyError("Queue not registered.")
    _registered_queues.pop(key)
    mq.remove()
    

def ipcs(options=[]):
    r"""Get the output from running the ipcs command.

    Args:
        options (list): List of flags that should be used. Defaults to an empty
            list.

    Returns:
        str: Captured output.

    """
    if _ipc_installed:
        cmd = ' '.join(['ipcs'] + options)
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
        output, err = p.communicate()
        exit_code = p.returncode
        if exit_code != 0:  # pragma: debug
            if not err.isspace():
                print(err.decode('utf-8'))
            raise Exception("Error on spawned process. See output.")
        return output.decode('utf-8')
    else:
        warn("IPC not installed. ipcs cannot be run.")
        return ''


def ipc_queues():
    r"""Get a list of active IPC queues.

    Returns:
       list: List of IPC queues.

    """
    skip_lines = [
        # Linux
        '------ Message Queues --------',
        'key        msqid      owner      perms      used-bytes   messages    ',
        # OSX
        'IPC status from',
        'Message Queues:',
        'T     ID     KEY        MODE       OWNER    GROUP']
    out = ipcs(['-q']).split('\n')
    qlist = []
    for l in out:
        skip = False
        if len(l) == 0:
            skip = True
        else:
            for ls in skip_lines:
                if ls in l:
                    skip = True
                    break
        if not skip:
            if platform._is_linux:
                key_col = 0
            elif platform._is_osx:
                key_col = 2
            else:  # pragma: debug
                raise NotImplementedError("Unsure what column the queue key " +
                                          "is in on this platform " +
                                          "(%s)" % sys.platform)
            qlist.append(l.split()[key_col])
    return qlist


def ipcrm(options=[]):
    r"""Remove IPC constructs using the ipcrm command.

    Args:
        options (list): List of flags that should be used. Defaults to an empty
            list.

    """
    if _ipc_installed:
        cmd = ' '.join(['ipcrm'] + options)
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
        output, err = p.communicate()
        exit_code = p.returncode
        if exit_code != 0:  # pragma: debug
            if not err.isspace():
                print(err.decode('utf-8'))
            raise Exception("Error on spawned process. See output.")
        if not output.isspace():
            print(output.decode('utf-8'))
    else:
        warn("IPC not installed. ipcrm cannot be run.")


def ipcrm_queues(queue_keys=None):
    r"""Delete existing IPC queues.

    Args:
        queue_keys (list, str, optional): A list of keys for queues that should
            be removed. Defaults to all existing queues.

    """
    if _ipc_installed:
        if queue_keys is None:
            queue_keys = ipc_queues()
        if isinstance(queue_keys, str):
            queue_keys = [queue_keys]
        for q in queue_keys:
            ipcrm(["-Q %s" % q])
    else:
        warn("IPC not installed. ipcrm cannot be run.")


class IPCComm(CommBase.CommBase):
    r"""Class for handling I/O via IPC message queues.

    Args:
        name (str): The name of the message queue.
        dont_open (bool, optional): If True, the connection will not be opened.
            Defaults to False.
        **kwargs: Additional keyword arguments are passed to CommBase.
        
    Attributes:
        q (:class:`sysv_ipc.MessageQueue`): Message queue.
        backlog_thread (threading.Thread): Thread that will handle sending
            or receiving backlogged messages.
        backlog_lock (threading.RLock): Lock for handling access of backlogs
            between threads.
        
    """
    def __init__(self, name, dont_open=False, **kwargs):
        super(IPCComm, self).__init__(name, dont_open=True, **kwargs)
        self.q = None
        self._bound = False
        self._backlog_recv = []
        self._backlog_send = []
        if self.direction == 'recv':
            self.backlog_thread = threading.Thread(target=self.run_backlog_recv)
        else:
            self.backlog_thread = threading.Thread(target=self.run_backlog_send)
        self.backlog_thread.daemon = True
        self.backlog_lock = threading.RLock()
        self.backlog_closed_event = threading.Event()
        self.backlog_send_ready = threading.Event()
        self.backlog_recv_ready = threading.Event()
        if dont_open:
            self.bind()
        else:
            self.open()

    @classmethod
    def is_installed(cls):
        r"""bool: Is the comm installed."""
        return _ipc_installed

    @property
    def maxMsgSize(self):
        r"""int: Maximum size of a single message that should be sent."""
        # Based on IPC limit on OSX
        return 2048
    
    @classmethod
    def comm_count(cls):
        r"""int: Total number of IPC queues started on this process."""
        return len(_registered_queues)

    @classmethod
    def new_comm_kwargs(cls, *args, **kwargs):
        r"""Initialize communication with new queue."""
        if 'address' not in kwargs:
            kwargs.setdefault('address', 'generate')
        return args, kwargs

    def bind(self):
        r"""Bind to random queue if address is generate."""
        self._bound = False
        if self.address == 'generate':
            self._bound = True
            q = get_queue()
            self.address = str(q.key)

    def open_after_bind(self):
        r"""Open the connection by getting the queue from the bound address."""
        qid = int(self.address)
        self.q = get_queue(qid)

    def open(self):
        r"""Open the connection by connecting to the queue."""
        super(IPCComm, self).open()
        if not self.is_open:
            if not self._bound:
                self.bind()
            self.open_after_bind()
            self.backlog_thread.start()
            self.debug("qid: %s", self.q.key)
            
    def close(self, wait_for_send=False):
        r"""Close the connection.

        Args:
            wait_for_send (bool, optional): If True, the thread will block
                until the queue is empty. Defaults to False.

        """
        if self._bound and not self.is_open:
            try:
                self.open_after_bind()
            except sysv_ipc.ExistentialError:  # pragma: debug
                self.q = None
                self._bound = False
        if self.is_open and not wait_for_send:
            # if wait_for_send:
            #     while self.n_msg_queued > 0:
            #         self.verbose_debug("Waiting for messages to be dequeued.")
            #         self.sleep()
            try:
                remove_queue(self.q)
            except (KeyError, sysv_ipc.ExistentialError):
                pass
            self.q = None
            self._bound = False
        self.backlog_closed_event.set()
        self.backlog_send_ready.set()
        self.backlog_recv_ready.set()
        super(IPCComm, self).close(wait_for_send=wait_for_send)
            
    @property
    def is_open(self):
        r"""bool: True if the queue is not None."""
        return (self.q is not None)

    @property
    def n_msg_queued(self):
        r"""int: Number of messages in the queue."""
        if self.is_open:
            try:
                return self.q.current_messages
            except sysv_ipc.ExistentialError:  # pragma: debug
                self.close()
                return 0
        else:
            return 0
        
    @property
    def n_msg_backlogged(self):
        r"""int: Number of backlogged messages."""
        if self.is_open:
            return len(self.backlog_recv)
        else:
            return 0

    @property
    def n_msg(self):
        r"""int: Number of messages in the queue and backlogged."""
        return self.n_msg_backlogged
        # return self.n_msg_queued + self.n_msg_backlogged

    @property
    def backlog_recv(self):
        r"""list: Messages that have been received."""
        with self.backlog_lock:
            return self._backlog_recv

    @property
    def backlog_send(self):
        r"""list: Messages that should be sent."""
        with self.backlog_lock:
            return self._backlog_send

    def add_backlog_recv(self, msg):
        r"""Add a message to the backlog of received messages.

        Args:
            msg (str): Received message that should be backlogged.

        """
        with self.backlog_lock:
            self.debug("Added %d bytes to recv backlog.", len(msg))
            self._backlog_recv.append(msg)
            self.backlog_recv_ready.set()

    def add_backlog_send(self, msg):
        r"""Add a message to the backlog of messages to be sent.

        Args:
            msg (str): Message that should be backlogged for sending.

        """
        with self.backlog_lock:
            self.debug("Added %d bytes to send backlog.", len(msg))
            self._backlog_send.append(msg)
            self.backlog_send_ready.set()

    def pop_backlog_recv(self):
        r"""Pop a message from the front of the recv backlog.

        Returns:
            str: First backlogged recv message.

        """
        with self.backlog_lock:
            msg = self._backlog_recv.pop(0)
            self.debug("Popped %d bytes from recv backlog.", len(msg))
            if len(self._backlog_recv) == 0:
                self.backlog_recv_ready.clear()
        return msg

    def pop_backlog_send(self):
        r"""Pop a message from the front of the send backlog.

        Returns:
            str: First backlogged send message.

        """
        with self.backlog_lock:
            msg = self._backlog_send.pop(0)
            self.debug("Popped %d bytes from send backlog.", len(msg))
            if len(self._backlog_send) == 0:
                self.backlog_send_ready.clear()
        return msg

    def run_backlog_send(self):
        r"""Continue trying to send buffered messages."""
        while True:
            flag = self.backlog_send_ready.wait(self.sleeptime)
            if (not self.is_open) or (self.backlog_closed_event.is_set()):
                break
            if flag:
                if not self.send_backlog():
                    break

    def run_backlog_recv(self):
        r"""Continue buffering received messages."""
        flag = True
        while self.is_open and flag and (not self.backlog_closed_event.is_set()):
            flag = self.recv_backlog()

    def send_backlog(self):
        r"""Send a message from the send backlog to the queue."""
        if len(self.backlog_send) == 0:
            return True
        try:
            flag = self._send(self.backlog_send[0], no_backlog=True)
            if flag:
                self.pop_backlog_send()
        except sysv_ipc.BusyError:  # pragma: debug
            self.debug('Queue full, failed to send backlogged message.')
            flag = True
        return flag

    def recv_backlog(self):
        r"""Check for any messages in the queue and add them to the recv
        backlog."""
        flag, data = self._recv(no_backlog=True)
        if flag and data:
            self.add_backlog_recv(data)
            self.debug('Backlogged received message.')
        return flag

    def _send(self, payload, no_backlog=False):
        r"""Send a message to the IPC queue.

        Args:
            payload (str): Message to send.
            no_backlog (bool, optional): If False, any messages that can't be
                sent because the queue is full will be added to a list of
                messages to be sent once the queue is no longer full. If True,
                messages are not backlogged and an error will be raised if the
                queue is full.

        Returns:
            bool: Success or failure of sending the message.

        """
        if not self.is_open:  # pragma: debug
            return False
        block = False
        if self.is_interface:
            no_backlog = True
            block = True
        try:
            if no_backlog or not self.backlog_send_ready.is_set():
                self.debug('Sending %d bytes', len(payload))
                self.q.send(payload, block=block)
            else:  # pragma: debug
                raise sysv_ipc.BusyError(
                    'Backlogged messages must be sent first')
        except sysv_ipc.BusyError:
            if no_backlog:
                self.debug('Could not send %d bytes', len(payload))
                # return False
                raise
            else:
                self.add_backlog_send(payload)
                self.debug('%d bytes backlogged', len(payload))
        except OSError:  # pragma: debug
            self.debug("Send failed")
            self.close()
            return False
        except AttributeError:  # pragma: debug
            if self.is_closed:
                return False
            raise
        return True

    def _recv(self, timeout=None, no_backlog=False):
        r"""Receive a message from the IPC queue.

        Args:
            timeout (float, optional): Time in seconds to wait for a message.
                Defaults to self.recv_timeout.
            no_backlog (bool, optional): If False and there are messages in the
                receive backlog, they will be returned first. Otherwise the
                queue is checked for a message.

        Returns:
            tuple (bool, str): The success or failure of receiving a message
                and the message received.

        """
        # If no backlog, receive from queue
        if no_backlog:
            # Return False if the queue is closed
            if self.is_closed:  # pragma: debug
                self.debug("Queue closed")
                return (False, self.empty_msg)
            # Return True, '' if there are no messages
            if self.n_msg_queued == 0:
                self.verbose_debug("No messages waiting.")
                return (True, self.empty_msg)
            # Receive message
            self.debug("Message ready, reading it.")
            try:
                data, _ = self.q.receive()  # ignore ident
                self.debug("Received %d bytes", len(data))
            except sysv_ipc.ExistentialError:  # pragma: debug
                self.debug("sysv_ipc.ExistentialError: closing")
                self.close()
                return (False, self.empty_msg)
            except AttributeError:  # pragma: debug
                if self.is_closed:
                    self.debug("Queue closed")
                    return (False, self.empty_msg)
                raise
            return (True, data)
        else:
            # Sleep until there is a message
            if timeout is None:
                timeout = self.recv_timeout
            if timeout is False:
                self.backlog_recv_ready.wait()
            else:
                self.backlog_recv_ready.wait(timeout)
            # Return False if the queue is closed
            if self.is_closed or self.backlog_closed_event.is_set():  # pragma: debug
                self.debug("Queue closed")
                return (False, self.empty_msg)
            # Return True, '' if there are no messages
            if not self.backlog_recv_ready.is_set():
                self.verbose_debug("No messages waiting.")
                return (True, self.empty_msg)
            # Return backlogged message
            # if len(self.backlog_recv) > 0:
            self.debug('Returning backlogged received message')
            return (True, self.pop_backlog_recv())

    def purge(self):
        r"""Purge all messages from the comm."""
        with self.backlog_lock:
            self.backlog_recv_ready.clear()
            self.backlog_send_ready.clear()
            self._backlog_recv = []
            self._backlog_send = []
        while self.n_msg_queued > 0:  # pragma: debug
            _, _ = self.q.receive()
        super(IPCComm, self).purge()
