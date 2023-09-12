import sys
import logging
from subprocess import Popen, PIPE
from yggdrasil import platform, tools
from yggdrasil.communication import (
    CommBase, TemporaryCommunicationError, NoMessages)
logger = logging.getLogger(__name__)
try:
    import sysv_ipc
    _ipc_installed = (platform._is_linux or platform._is_mac)
except ImportError:  # pragma: windows
    logger.debug("Could not import sysv_ipc."
                 " IPC support will be disabled.")
    sysv_ipc = None
    _ipc_installed = False


def get_queue(qid=None):
    r"""Create or return a sysv_ipc.MessageQueue and register it.

    Args:
        qid (int, optional): If provided, ID for existing queue that should be
           returned. Defaults to None and a new queue is returned.

    Returns:
        :class:`sysv_ipc.MessageQueue`: Message queue.

    """
    if _ipc_installed:
        kwargs = dict(max_message_size=tools.get_YGG_MSG_MAX())
        if qid is None:
            kwargs['flags'] = sysv_ipc.IPC_CREX
        try:
            mq = sysv_ipc.MessageQueue(qid, **kwargs)
        except sysv_ipc.ExistentialError as e:  # pragma: debug
            raise sysv_ipc.ExistentialError(f"{e}: {qid}")
        key = str(mq.key)
        IPCComm.register_comm(key, mq)
        return mq
    else:  # pragma: windows
        logger.warning("IPC not installed. Queue cannot be returned.")
        return None


def remove_queue(mq):
    r"""Remove a sysv_ipc.MessageQueue and unregister it.

    Args:
        mq (:class:`sysv_ipc.MessageQueue`) Message queue.
    
    Raises:
        KeyError: If the provided queue is not registered.

    """
    key = str(mq.key)
    if not IPCComm.is_registered(key):
        raise KeyError("Queue not registered.")
    IPCComm.unregister_comm(key)
    

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
    else:  # pragma: windows
        logger.warn("IPC not installed. ipcs cannot be run.")
        return ''


def ipc_queues(by_id=False):
    r"""Get a list of active IPC queues.

    Returns:
       list: List of IPC queues.

    """
    skip_lines = [
        # Linux
        '------ Message Queues --------',
        'key        msqid      owner      perms      used-bytes   messages    ',
        # MacOS
        'IPC status from',
        'Message Queues:',
        'T     ID     KEY        MODE       OWNER    GROUP']
    out = ipcs(['-q']).split('\n')
    qlist = []
    for line in out:
        skip = False
        if len(line) == 0:
            skip = True
        else:
            for ls in skip_lines:
                if ls in line:
                    skip = True
                    break
        if not skip:
            if platform._is_linux:
                if by_id:
                    key_col = 1
                else:
                    key_col = 0
            elif platform._is_mac:
                if by_id:
                    key_col = 1
                else:
                    key_col = 2
            else:  # pragma: debug
                raise NotImplementedError("Unsure what column the queue key "
                                          + "is in on this platform "
                                          + "(%s)" % sys.platform)
            qlist.append(line.split()[key_col])
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
    else:  # pragma: windows
        logger.warn("IPC not installed. ipcrm cannot be run.")


def ipcrm_queues(queue_keys=None, by_id=False):
    r"""Delete existing IPC queues.

    Args:
        queue_keys (list, str, optional): A list of keys for queues that should
            be removed. Defaults to all existing queues.

    """
    if _ipc_installed:
        if queue_keys is None:
            queue_keys = ipc_queues(by_id=by_id)
        if isinstance(queue_keys, str):
            queue_keys = [queue_keys]
        if by_id:
            flags = '-q'
        else:
            flags = '-Q'
        for q in queue_keys:
            ipcrm([f"{flags} {q}"])
    else:  # pragma: windows
        logger.warn("IPC not installed. ipcrm cannot be run.")


class IPCServer(CommBase.CommServer):
    r"""IPC server object for cleaning up server queue."""

    def terminate(self, *args, **kwargs):
        IPCComm.unregister_comm(self.srv_address)
        super(IPCServer, self).terminate(*args, **kwargs)


class IPCComm(CommBase.CommBase):
    r"""Class for handling I/O via IPC message queues.

    Attributes:
        q (:class:`sysv_ipc.MessageQueue`): Message queue.

    Developer Notes:
        The default size limit for IPC message queues is 2048 bytes on Mac
        operating systems so it is important that implementation of this
        communication mechanism properly split and send messages larger than
        this limit as more than one message.
        
    """

    _commtype = 'ipc'
    _schema_subtype_description = ('Interprocess communication (IPC) queue.')
    _maxMsgSize = 2048  # Based on IPC limit on MacOS
    address_description = ("An IPC message queue key.")
    _deprecated_drivers = ['IPCInputDriver', 'IPCOutputDriver']

    def _init_before_open(self, **kwargs):
        r"""Initialize empty queue and server class."""
        self.q = None
        self._server_class = IPCServer
        super(IPCComm, self)._init_before_open(**kwargs)
            
    @classmethod
    def close_registry_entry(cls, value):
        r"""Close a registry entry."""
        try:
            value.remove()
            out = True
        except sysv_ipc.ExistentialError:  # pragma: debug
            out = False
        return out

    @classmethod
    def new_comm_kwargs(cls, *args, **kwargs):
        r"""Initialize communication with new queue."""
        if 'address' not in kwargs:
            kwargs.setdefault('address', 'generate')
        return args, kwargs

    def bind(self):
        r"""Bind to random queue if address is generate."""
        if not self._bound:
            if self.address == 'generate':
                self._bound = True
                q = get_queue()
                self.address = str(q.key)
        super(IPCComm, self).bind()

    def open_after_bind(self):
        r"""Open the connection by getting the queue from the bound address."""
        qid = int(self.address)
        self.q = get_queue(qid)

    def open(self):
        r"""Open the queue."""
        super(IPCComm, self).open()
        if not self.is_open:
            self.open_after_bind()
            self.debug("qid: %s", self.q.key)

    def _close(self, linger=False, skip_remove=False):
        r"""Close the queue."""
        if self._bound and (self.q is None):
            try:
                self.open_after_bind()
            except sysv_ipc.ExistentialError:  # pragma: debug
                self.q = None
                self._bound = False
        # Remove the queue
        dont_close = (skip_remove or self.is_client)
        if (self.q is not None) and (not dont_close):
            # Dont close for client because server will not be able
            # to unregister the comm
            self.unregister_comm(self.address, dont_close=dont_close)
        self.q = None
        self._bound = False
        super(IPCComm, self)._close(linger=linger)

    def atexit(self):  # pragma: debug
        r"""Close operations."""
        if self.direction == 'send':
            self.linger()
        super(IPCComm, self).atexit()
        
    @property
    def is_open(self):
        r"""bool: True if the queue is not None."""
        if self.q is None:
            return False
        try:
            self.q.current_messages
        except AttributeError:  # pragma: debug
            if self.q is not None:
                raise
            return False
        except sysv_ipc.ExistentialError:  # pragma: debug
            self._close()
            return False
        return True

    def confirm_send(self, noblock=False):
        r"""Confirm that sent message was received."""
        if noblock:
            return True
        return (self.n_msg_send == 0)

    def confirm_recv(self, noblock=False):
        r"""Confirm that message was received."""
        return True

    @property
    def n_msg_send(self):
        r"""int: Number of messages in the queue to send."""
        if self.is_open:
            try:
                return self.q.current_messages
            except AttributeError:  # pragma: debug
                if self.is_open:
                    raise
                return 0
            except sysv_ipc.ExistentialError:  # pragma: debug
                self._close()
                return 0
        else:
            return 0
        
    @property
    def n_msg_recv(self):
        r"""int: Number of messages in the queue to recv."""
        return self.n_msg_send

    def _send(self, payload):
        r"""Send a message.

        Args:
            payload (str): Message to send.

        Returns:
            bool: Success or failure of sending the message.

        """
        try:
            self.q.send(payload, block=False)
        except sysv_ipc.BusyError:  # pragma: debug
            raise TemporaryCommunicationError("Queue full.")
        return True

    def _recv(self):
        r"""Receive a message from the IPC queue.

        Returns:
            tuple (bool, str): The success or failure of receiving a message
                and the message received.

        """
        try:
            data, _ = self.q.receive(block=False)  # ignore ident
        except sysv_ipc.BusyError:  # pragma: debug
            raise NoMessages("No messages in queue.")
        return (True, data)

    def purge(self):
        r"""Purge all messages from the comm."""
        super(IPCComm, self).purge()
        try:
            while self.n_msg > 0:  # pragma: debug
                self.q.receive()
        except AttributeError:  # pragma: debug
            if self.is_open:
                raise
