from yggdrasil.communication import MultiComm


class ForkComm(MultiComm.MultiComm):
    r"""Class for receiving/sending messages from/to multiple comms.

    Args:
        name (str): The environment variable where communication address is
            stored.
        comm (list, optional): The list of options for the comms that
            should be bundled. If not provided, the bundle will be empty.
        **kwargs: Additional keyword arguments are passed to the parent class.

    Attributes:
        comm_list (list): Comms included in this fork.
        curr_comm_index (int): Index comm that next receive will be from.

    """

    def __init__(self, *args, **kwargs):
        super(ForkComm, self).__init__(*args, **kwargs)
        self.curr_comm_index = 0
        self.eof_recv = [0 for _ in self.comm_list]
        assert(not self.composite)

    @property
    def curr_comm(self):
        r"""CommBase: Current comm."""
        return self.comm_list[self.curr_comm_index % len(self)]

    def get_field_names(self):
        r"""Determine the field names associated with messages that will
        be sent/received by this comm.

        Returns:
            list: Field names.

        """
        out = None
        if len(self) > 0:
            out = self.comm_list[0].get_field_names()
        return out
        
    @property
    def is_open(self):
        r"""bool: True if the connection is open."""
        for x in self.comm_list:
            if x.is_open:
                return True
        return False
    
    @property
    def n_msg_recv(self):
        r"""int: The number of incoming messages in the connection."""
        return sum([x.n_msg_recv for x in self.comm_list])

    @property
    def n_msg_send(self):
        r"""int: The number of outgoing messages in the connection."""
        return sum([x.n_msg_send for x in self.comm_list])

    @property
    def n_msg_recv_drain(self):
        r"""int: The number of incoming messages in the connection to drain."""
        return sum([x.n_msg_recv_drain for x in self.comm_list])

    @property
    def n_msg_send_drain(self):
        r"""int: The number of outgoing messages in the connection to drain."""
        return sum([x.n_msg_send_drain for x in self.comm_list])

    def send_multipart(self, msg, **kwargs):
        r"""Send a message.

        Args:
            msg (obj): Message to be sent.
            **kwargs: All keywords arguments are passed to comm _send method.

        Returns:
            bool: Success or failure of send.

        """
        is_single = (len(msg) == 1)
        if is_single:
            msg = msg[0]
        msg = self.apply_send_converter(msg)
        if is_single:
            msg = (msg, )
        for x in self.comm_list:
            out = x.send(*msg, **kwargs)
            if not out:
                return out
        return out

    def recv_multipart(self, *args, **kwargs):
        r"""Receive a message.

        Args:
            *args: All arguments are passed to comm _recv method.
            **kwargs: All keywords arguments are passed to comm _recv method.

        Returns:
            tuple (bool, obj): Success or failure of receive and received
                message.

        """
        timeout = kwargs.pop('timeout', None)
        if timeout is None:
            timeout = self.recv_timeout
        kwargs['timeout'] = 0
        first_comm = True
        T = self.start_timeout(timeout, key_suffix='recv:forkd')
        out = None
        while ((not T.is_out) or first_comm) and self.is_open and (out is None):
            for i in range(len(self)):
                if out is not None:
                    break
                x = self.curr_comm
                if x.is_open:
                    flag, msg = x.recv(*args, **kwargs)
                    if x.is_eof(msg):
                        self.eof_recv[self.curr_comm_index % len(self)] = 1
                        if sum(self.eof_recv) == len(self):
                            out = (self.on_recv_eof(), self.eof_msg)
                    elif (not x.is_empty_recv(msg)):
                        out = (flag, self.apply_recv_converter(msg))
                self.curr_comm_index += 1
            first_comm = False
            if out is None:
                self.sleep()
        self.stop_timeout(key_suffix='recv:forkd')
        if out is None:
            if self.is_closed:
                self.debug('Comm closed')
                out = (False, None)
            else:
                out = (True, self.empty_obj_recv)
        return out
