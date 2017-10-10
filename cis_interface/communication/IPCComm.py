import sysv_ipc
from subprocess import Popen, PIPE
from cis_interface import backwards, tools
from cis_interface.communication import CommBase


_N_QUEUES = 0
_registered_queues = {}


def get_queue(qid=None):
    r"""Create or return a sysv_ipc.MessageQueue and register it.

    Args:
        qid (int, optional): If provided, ID for existing queue that should be
           returned. Defaults to None and a new queue is returned.

    Returns:
        :class:`sysv_ipc.MessageQueue`: Message queue.

    """
    kwargs = dict(max_message_size=tools.PSI_MSG_MAX)
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
        
    """
    def __init__(self, name, dont_open=False, **kwargs):
        super(IPCComm, self).__init__(name, dont_open=True, **kwargs)
        self.q = None
        if not dont_open:
            self.open()

    @property
    @staticmethod
    def comm_count(cls):
        r"""int: Total number of IPC queues started on this process."""
        return _N_QUEUES

    @classmethod
    def new_comm_kwargs(cls, *args, **kwargs):
        r"""Initialize communication with new queue."""
        global _N_QUEUES
        if 'address' not in kwargs:
            q = get_queue()
            kwargs['address'] = str(q.key)
            _N_QUEUES += 1
        # kwargs.setdefault('address', 'generate')
        return args, kwargs

    def open(self):
        r"""Open the connection by connecting to the queue."""
        global _N_QUEUES
        if not self.is_open:
            if self.address == 'generate':
                self.q = get_queue()
                self.address = str(self.q.key)
                _N_QUEUES += 1
            else:
                qid = int(self.address)
                self.q = get_queue(qid)
            self.debug(": qid %s", self.q.key)

    def close(self):
        r"""Close the connection."""
        if self.is_open:
            try:
                remove_queue(self.q)
            except KeyError:
                pass
            self.q = None
            
    @property
    def is_open(self):
        r"""bool: True if the queue is not None."""
        return (self.q is not None)

    @property
    def n_msg(self):
        r"""int: Number of messages in the queue."""
        if self.is_open:
            return self.q.current_messages
        else:
            return 0

    def _recv(self, timeout=0):
        r"""Receive a message smaller than PSI_MSG_MAX. The process will
        sleep until there is a message in the queue to receive.

        Returns:
            tuple (bool, str): The success or failure of receiving a message
                and the message received.

        """
        # Sleep until there is a message
        Tout = self.start_timeout(timeout)
        while self.n_msg == 0 and self.is_open and (not Tout.is_out):
            # self.debug("recv(): no data, sleep")
            self.sleep()
        self.stop_timeout()
        # Return False if the queue is closed
        if self.is_closed:
            self.debug("recv(): queue closed, returning (False, '')")
            return (False, '')
        # Return True, '' if there are no messages
        if self.n_msg == 0:
            self.debug("recv(): no data, returning (True, '')")
            return (True, '')
        # Receive message
        self.debug(".recv(): message ready, read it")
        data, _ = self.q.receive()  # ignore ident
        return (True, data)

    def _recv_nolimit(self, *args, **kwargs):
        r"""Receive a message larger than PSI_MSG_MAX that is sent in multiple
        parts.

        Args:
            *args: All arguments are passed to _recv.
            **kwargs: All keyword arguments are passed to _recv.

        Returns:
            tuple (bool, str): The success or failure of receiving a message
                and the complete message received.

        """
        self.debug(".recv_nolimit()")
        payload = self._recv(*args, **kwargs)
        if not payload[0] or (len(payload[1]) == 0):  # pragma: debug
            self.debug(".recv_nolimit(): Failed to receive payload size.")
            return payload
        leng_exp = int(float(payload[1]))
        data = backwards.unicode2bytes('')
        ret = True
        while len(data) < leng_exp:
            payload = self._recv(*args, **kwargs)
            if not payload[0]:  # pragma: debug
                self.debug(
                    ".recv_nolimit(): read interupted at %d of %d bytes.",
                    len(data), leng_exp)
                ret = False
                break
            data = data + payload[1]
        payload = (ret, data)
        self.debug(".recv_nolimit(): read %d bytes", len(data))
        return payload

    def _send(self, payload):
        r"""Send a message smaller than PSI_MSG_MAX.

        Args:
            payload (str): Message to send.

        Returns:
            bool: Success or failure of sending the message.

        """
        if not self.is_open:
            return False
        else:
            self.q.send(payload)
            return True

    def _send_nolimit(self, payload):
        r"""Send a message larger than PSI_MSG_MAX in multiple parts.

        Args:
            payload (str): Message to send.

        Returns:
            bool: Success or failure of sending the message.

        """
        ret = self._send("%ld" % len(payload))
        if not ret:  # pragma: debug
            self.debug(".send_nolimit: Sending size of payload failed.")
            return ret
        nsent = 0
        for imsg in self.chunk_message(payload):
            ret = self._send(imsg)
            if not ret:  # pragma: debug
                self.debug(
                    ".send_nolimit(): send interupted at %d of %d bytes.",
                    nsent, len(payload))
                break
            nsent += len(imsg)
            self.debug(".send_nolimit(): %d of %d bytes sent",
                       nsent, len(payload))
        if ret:
            self.debug(".send_nolimit %d bytes completed", len(payload))
        return ret
