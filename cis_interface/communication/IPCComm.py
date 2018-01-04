import sysv_ipc
import threading
from subprocess import Popen, PIPE
from cis_interface.tools import CIS_MSG_MAX, is_ipc_installed
from cis_interface.communication import CommBase


_registered_queues = {}


def get_queue(qid=None):
    r"""Create or return a sysv_ipc.MessageQueue and register it.

    Args:
        qid (int, optional): If provided, ID for existing queue that should be
           returned. Defaults to None and a new queue is returned.

    Returns:
        :class:`sysv_ipc.MessageQueue`: Message queue.

    """
    global _registered_queues
    kwargs = dict(max_message_size=CIS_MSG_MAX)
    if qid is None:
        kwargs['flags'] = sysv_ipc.IPC_CREX
    mq = sysv_ipc.MessageQueue(qid, **kwargs)
    key = str(mq.key)
    if key not in _registered_queues:
        _registered_queues[key] = mq
    return mq


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
        list: Captured output.

    """
    cmd = ' '.join(['ipcs'] + options)
    p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
    output, err = p.communicate()
    exit_code = p.returncode
    if exit_code != 0:  # pragma: debug
        if not err.isspace():
            print(err.decode('utf-8'))
        raise Exception("Error on spawned process. See output.")
    return output.decode('utf-8')


def ipc_queues():
    r"""Get a list of active IPC queues.

    Returns:
       list: List of IPC queues.

    """
    skip_lines = [
        '------ Message Queues --------',
        'key        msqid      owner      perms      used-bytes   messages    ',
        '']
    out = ipcs(['-q']).split('\n')
    qlist = []
    for l in out:
        if l not in skip_lines:
            qlist.append(l)
    return qlist


def ipcrm(options=[]):
    r"""Remove IPC constructs using the ipcrm command.

    Args:
        options (list): List of flags that should be used. Defaults to an empty
            list.

    """
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


def ipcrm_queues(queue_keys=None):
    r"""Delete existing IPC queues.

    Args:
        queue_keys (list, str, optional): A list of keys for queues that should
            be removed. Defaults to all existing queues.

    """
    if queue_keys is None:
        queue_keys = [l.split()[0] for l in ipc_queues()]
    if isinstance(queue_keys, str):
        queue_keys = [queue_keys]
    for q in queue_keys:
        ipcrm(["-Q %s" % q])


class IPCComm(CommBase.CommBase):
    r"""Class for handling I/O via IPC message queues.

    Args:
        name (str): The name of the message queue.
        dont_open (bool, optional): If True, the connection will not be opened.
            Defaults to False.
        **kwargs: Additional keyword arguments are passed to CommBase.
        
    Attributes:
        q (:class:`sysv_ipc.MessageQueue`): Message queue.
        backlog_recv (list): A list of messages that have been received.
        backlog_send (list): A list of messages that should be sent.
        backlog_thread (threading.Thread): Thread that will handle sending
            or receiving backlogged messages.
        
    """
    def __init__(self, name, dont_open=False, **kwargs):
        super(IPCComm, self).__init__(name, dont_open=True, **kwargs)
        self.q = None
        self._bound = False
        self.backlog_recv = []
        self.backlog_send = []
        self.backlog_thread = threading.Thread(target=self.run_backlog)
        if dont_open:
            self.bind()
        else:
            self.open()

    @classmethod
    def is_installed(cls):
        r"""bool: Is the comm installed."""
        return is_ipc_installed()

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
            
    def close(self):
        r"""Close the connection."""
        if self._bound and not self.is_open:
            try:
                self.open_after_bind()
            except sysv_ipc.ExistentialError:  # pragma: debug
                self.q = None
                self._bound = False
        if self.is_open:
            try:
                remove_queue(self.q)
            except (KeyError, sysv_ipc.ExistentialError):
                pass
            self.q = None
            self._bound = False
        super(IPCComm, self).close()
            
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
            return len(self.backlog_recv) + len(self.backlog_send)
        else:
            return 0

    @property
    def n_msg(self):
        r"""int: Number of messages in the queue and backlogged."""
        return self.n_msg_queued + self.n_msg_backlogged

    def run_backlog(self):
        r"""Continue checking for buffered messages to be sent/recveived."""
        flag = True
        while self.is_open and flag:
            if self.direction == 'recv':
                flag = self.recv_backlog()
            else:
                flag = self.send_backlog()
            self.sleep()

    def send_backlog(self):
        r"""Send a message from the send backlog to the queue."""
        if len(self.backlog_send) == 0:
            return True
        try:
            flag = self._send(self.backlog_send[0], no_backlog=True)
            if flag:
                self.backlog_send.pop(0)
        except sysv_ipc.BusyError:
            pass
        return True

    def recv_backlog(self):
        r"""Check for any messages in the queue and add them to the recv
        backlog."""
        flag, data = self._recv(no_backlog=True)
        if flag and data:
            self.backlog_recv.append(data)
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
        try:
            if no_backlog or len(self.backlog_send) == 0:
                self.q.send(payload, block=False)
            else:
                raise sysv_ipc.BusyError(
                    'Backlogged messages must be received first')
        except sysv_ipc.BusyError:
            if no_backlog:
                return False
            else:
                self.backlog_send.append(payload)
                self.debug('%d bytes backlogged', len(payload))
        except OSError:  # pragma: debug
            # self.debug("Send failed")
            self.close()
            return False
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
        # Sleep until there is a message
        if timeout is None:
            timeout = self.recv_timeout
        if not no_backlog:
            Tout = self.start_timeout(timeout)
            while self.n_msg == 0 and self.is_open and (not Tout.is_out):
                # self.debug("No data, sleeping")
                self.sleep()
            self.stop_timeout()
        # Return False if the queue is closed
        if self.is_closed:  # pragma: debug
            self.debug("Queue closed")
            return (False, self.empty_msg)
        # Return backlogged message
        if (not no_backlog) and (len(self.backlog_recv) > 0):
            self.debug('Returning backlogged message')
            return (True, self.backlog_recv.pop(0))
        # Return True, '' if there are no messages
        if self.n_msg_queued == 0:
            self.verbose_debug("No messages waiting.")
            return (True, self.empty_msg)
        # Receive message
        self.debug("Message ready, reading it.")
        try:
            data, _ = self.q.receive()  # ignore ident
        except sysv_ipc.ExistentialError:  # pragma: debug
            self.close()
            return (False, self.empty_msg)
        return (True, data)

    def purge(self):
        r"""Purge all messages from the comm."""
        self.backlog_recv = []
        self.backlog_send = []
        while self.n_msg_queued > 0:
            _, _ = self.q.receive()
        super(IPCComm, self).purge()
