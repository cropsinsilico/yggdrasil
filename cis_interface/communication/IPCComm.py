from logging import debug  # , error, exception
import time
import sysv_ipc
from cis_interface import backwards, tools
from cis_interface.communication import CommBase


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

    @classmethod
    def new_comm(cls, name):
        r"""Initialize communication with new queue.

        Args:
            name (str): The name of the message queue.

        Returns:
            IPCComm: Instance with new queue.

        """
        q = tools.get_queue()
        out = cls(name, address=str(q.key))
        return out

    def open(self):
        r"""Open the connection by connecting to the queue."""
        if not self.is_open:
            qid = int(self.address)
            debug("IPCComm(%s): qid %s", self.name, qid)
            self.q = tools.get_queue(qid)

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

    def _recv(self):
        r"""Receive a message smaller than PSI_MSG_MAX. The process will
        sleep until there is a message in the queue to receive.

        Returns:
            tuple (bool, str): The success or failure of receiving a message
                and the message received.

        """
        payload = (False, '')
        debug("IPCComm(%s).recv()", self.name)
        try:
            while self.n_msg == 0 and self.is_open:
                debug("IPCComm(%s): recv() - no data, sleep", self.name)
                time.sleep(self.sleeptime)
            debug("IPCComm(%s).recv(): message ready, read it", self.name)
            data, _ = self.q.receive()  # ignore ident
            payload = (True, data)
            debug("IPCComm(%s).recv(): read %d bytes", self.name, len(data))
        except sysv_ipc.ExistentialError:  # pragma: debug
            debug("IPCComm(%s).recv(): queue closed, returning (False, '')",
                  self.name)
        except Exception as ex:  # pragma: debug
            # debug("IPCComm(%s).recv(): exception %s, return None", self.name, type(ex))
            raise ex
        return payload

    def _recv_nolimit(self):
        r"""Receive a message larger than PSI_MSG_MAX that is sent in multiple
        parts.

        Returns:
            tuple (bool, str): The success or failure of receiving a message
                and the complete message received.

        """
        debug("IPCComm(%s).recv_nolimit()", self.name)
        payload = self.recv()
        if not payload[0]:  # pragma: debug
            debug("IPCComm(%s).recv_nolimit(): " +
                  "Failed to receive payload size.", self.name)
            return payload
        leng_exp = int(float(payload[1]))
        data = backwards.unicode2bytes('')
        ret = True
        while len(data) < leng_exp:
            payload = self.recv()
            if not payload[0]:  # pragma: debug
                debug("IPCComm(%s).recv_nolimit(): " +
                      "read interupted at %d of %d bytes.",
                      self.name, len(data), leng_exp)
                ret = False
                break
            data = data + payload[1]
        payload = (ret, data)
        debug("IPCComm(%s).recv_nolimit(): read %d bytes",
              self.name, len(data))
        return payload

    def _send(self, payload):
        r"""Send a message smaller than PSI_MSG_MAX.

        Args:
            payload (str): Message to send.

        Returns:
            bool: Success or failure of sending the message.

        """
        max_msg = 10
        if len(payload) > max_msg:
            payload_msg = payload[:max_msg] + ' ...'
        else:
            payload_msg = payload
        ret = False
        try:
            debug("IPCComm(%s).send(%s)", self.name, payload_msg)
            self.q.send(payload)
            ret = True
            debug("IPCComm(%s).sent(%s)", self.name, payload_msg)
        except Exception as ex:  # pragma: debug
            debug("IPCComm(%s).send(%s): exception: %s", self.name, payload_msg, type(ex))
            raise ex
        debug("IPCComm(%s).send(%s): returns %d", self.name, payload_msg, ret)
        return ret

    def _send_nolimit(self, payload):
        r"""Send a message larger than PSI_MSG_MAX in multiple parts.

        Args:
            payload (str): Message to send.

        Returns:
            bool: Success or failure of sending the message.

        """
        ret = self.send("%ld" % len(payload))
        if not ret:  # pragma: debug
            debug("IPCComm(%s).send_nolimit: " +
                  "Sending size of payload failed.", self.name)
            return ret
        nsent = 0
        for imsg in self.chunk_message(payload):
            ret = self.send(imsg)
            if not ret:  # pragma: debug
                debug("IPCComm(%s).send_nolimit(): " +
                      "send interupted at %d of %d bytes.",
                      self.name, nsent, len(payload))
                break
            nsent += len(imsg)
            debug("IPCComm(%s).send_nolimit(): %d of %d bytes sent",
                  self.name, nsent, len(payload))
        if ret:
            debug("IPCComm(%s).send_nolimit %d bytes completed",
                  self.name, len(payload))
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
