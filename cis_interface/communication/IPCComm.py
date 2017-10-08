import sysv_ipc
from cis_interface import backwards, tools
from cis_interface.communication import CommBase


_N_QUEUES = 0


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
    def new_comm(cls, name, **kwargs):
        r"""Initialize communication with new queue.

        Args:
            name (str): The name of the message queue.

        Returns:
            IPCComm: Instance with new queue.

        """
        kwargs.setdefault('address', 'generate')
        out = cls(name, **kwargs)
        return out

    def open(self):
        r"""Open the connection by connecting to the queue."""
        global _N_QUEUES
        if not self.is_open:
            if self.address == 'generate':
                self.q = tools.get_queue()
                self.address = str(self.q.key)
                _N_QUEUES += 1
            else:
                qid = int(self.address)
                self.q = tools.get_queue(qid)
            self.debug(": qid %s", self.q.key)

    def close(self):
        r"""Close the connection."""
        if self.is_open:
            try:
                tools.remove_queue(self.q)
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
            self.debug("recv(): no data, sleep")
            self.sleep()
        self.stop_timeout()
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


class IPCInput(IPCComm):
    r"""Class for handling input via an IPC queue.

    Args:
        name (str): The environment variable where the queue ID is stored.
        **kwargs: All additional keywords are passed to IPCComm.

    """
    def __init__(self, name, **kwargs):
        super(IPCInput, self).__init__(name + "_IN", **kwargs)

        
class IPCOutput(IPCComm):
    r"""Class for handling output via an IPC queue.

    Args:
        name (str): The environment variable where the queue ID is stored.
        **kwargs: All additional keywords are passed to IPCComm.
    """
    def __init__(self, name, **kwargs):
        super(IPCOutput, self).__init__(name + "_OUT", **kwargs)
