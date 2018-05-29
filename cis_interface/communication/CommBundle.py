from cis_interface.communication import CommBase, get_comm, get_comm_class


_address_sep = ':CIS_ADD:'


def get_comm_name(name, i):
    r"""Get the name of the ith comm in the series.

    Args:
        name (str): Name of the bundle comm.
        i (int): Index of comm in bundle.

    Returns:
        str: Name of ith comm in bundle.

    """
    return '%s_%d' % (name, i)


class CommBundle(CommBase.CommBase):
    r"""Class for receiving/sending messages from/to multiple comms.

    Args:
        name (str): The environment variable where communication address is
            stored.
        comm_kwargs (list, optional): The list of options for the comms that
            should be bundled. If not provided, the bundle will be empty.
        **kwargs: Additional keyword arguments are passed to the parent class.

    Attributes:
        comm_list (list): Comms included in this bundle.
        curr_comm_index (int): Index comm that next receive will be from.

    """
    def __init__(self, name, **kwargs):
        self.comm_list = []
        self.curr_comm_index = 0
        self.eof_recv = []
        super(CommBundle, self).__init__(name, **kwargs)

    def _init_before_open(self, comm_kwargs=None, **kwargs):
        r"""Initialization steps that should be performed after base class, but
        before the comm is opened."""
        super(CommBundle, self)._init_before_open(**kwargs)
        assert(not self.single_use)
        assert(not self.is_server)
        assert(not self.is_client)
        if comm_kwargs is None:
            comm_kwargs = [dict() for _ in range(len(self))]
        assert(len(comm_kwargs) == len(self))
        for i in range(len(self)):
            ikw = dict(**kwargs)
            ikw['address'] = self.address_list[i]
            if comm_kwargs[i] is not None:
                ikw.update(**comm_kwargs[i])
            iname = get_comm_name(self.name, i)
            self.comm_list.append(get_comm(iname, **ikw))
            self.eof_recv.append(0)
            
    def __len__(self):
        return len(self.address_list)

    @property
    def curr_comm(self):
        r"""CommBase: Current comm."""
        return self.comm_list[self.curr_comm_index % len(self)]

    @property
    def address_list(self):
        r"""list: List of addresses for comms in this bundle."""
        return self.address.split(_address_sep)

    @property
    def maxMsgSize(self):
        r"""int: Maximum size of a single message that should be sent."""
        return min([x.maxMsgSize for x in self.comm_list])

    @classmethod
    def new_comm_kwargs(cls, name, *args, **kwargs):
        r"""Get keyword arguments for new comm."""
        if 'address' not in kwargs:
            addresses = []
            comm_kwargs = []
            for i, x in enumerate(kwargs.get('comm_kwargs', [])):
                iname = get_comm_name(name, i)
                icls = get_comm_class(x.get('comm', None))
                _, ickw = icls.new_comm_kwargs(iname, **x)
                comm_kwargs.append(ickw)
                addresses.append(ickw['address'])
            kwargs['comm_kwargs'] = comm_kwargs
            kwargs['address'] = _address_sep.join(addresses)
        args = tuple([name] + list(args))
        return args, kwargs

    def opp_comm_kwargs(self):
        r"""Get keyword arguments to initialize communication with opposite
        comm object.

        Returns:
            dict: Keyword arguments for opposite comm object.

        """
        kwargs = super(CommBundle, self).opp_comm_kwargs()
        kwargs['comm_kwargs'] = [x.opp_comm_kwargs() for x in self.comm_list]
        return kwargs

    def bind(self):
        r"""Bind in place of open."""
        for x in self.comm_list:
            x.bind()

    def open(self):
        r"""Open the connection."""
        for x in self.comm_list:
            x.open()

    def close(self, *args, **kwargs):
        r"""Close the connection."""
        for x in self.comm_list:
            x.close(*args, **kwargs)

    def close_in_thread(self, *args, **kwargs):
        r"""In a new thread, close the comm when it is empty."""
        for x in self.comm_list:
            x.close_in_thread(*args, **kwargs)

    @property
    def is_open(self):
        r"""bool: True if the connection is open."""
        for x in self.comm_list:
            if x.is_open:
                return True
        return False

    @property
    def is_confirmed_send(self):
        r"""bool: True if all sent messages have been confirmed."""
        for x in self.comm_list:
            if not x.is_confirmed_send:
                return False
        return True

    @property
    def is_confirmed_recv(self):
        r"""bool: True if all received messages have been confirmed."""
        for x in self.comm_list:
            if not x.is_confirmed_recv:
                return False
        return True

    def confirm_send(self, noblock=False):
        r"""Confirm that sent message was received."""
        for x in self.comm_list:
            if not x.confirm_send(noblock=noblock):
                return False
        return True

    def confirm_recv(self, noblock=False):
        r"""Confirm that message was received."""
        for x in self.comm_list:
            if not x.confirm_recv(noblock=noblock):
                return False
        return True

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

    @property
    def empty_obj_recv(self):
        r"""obj: Empty message object."""
        emsg, _ = self.serializer.deserialize(self.empty_msg)
        if (self.recv_converter is not None):
            emsg = self.recv_converter(emsg)
        return emsg

    def is_empty_recv(self, msg):
        r"""Check if a received message object is empty.

        Args:
            msg (obj): Message object.

        Returns:
            bool: True if the object is empty, False otherwise.

        """
        if self.is_eof(msg):
            return False
        return (msg == self.empty_obj_recv)
    
    def send(self, *args, **kwargs):
        r"""Send a message.

        Args:
            *args: All arguments are assumed to be part of the message.
            **kwargs: All keywords arguments are passed to comm _send method.

        Returns:
            bool: Success or failure of send.

        """
        for x in self.comm_list:
            out = x.send(*args, **kwargs)
            if not out:
                return out
        return out

    def recv(self, *args, **kwargs):
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
        T = self.start_timeout(timeout, key_suffix='recv:bundled')
        out = None
        while ((not T.is_out) or first_comm) and self.is_open and (out is None):
            for i in range(len(self)):
                if out is not None:
                    break
                x = self.curr_comm
                if x.is_open:
                    flag, msg = x.recv(*args, **kwargs)
                    if self.is_eof(msg):
                        self.eof_recv[self.curr_comm_index % len(self)] = 1
                        if sum(self.eof_recv) == len(self):
                            out = (flag, msg)
                            break
                    elif (not self.is_empty_recv(msg)):
                        out = (flag, msg)
                        break
                self.curr_comm_index += 1
            first_comm = False
            self.sleep()
        self.stop_timeout(key_suffix='recv:bundled')
        if out is None:
            if self.is_closed:
                self.debug('Comm closed')
                out = (False, None)
            else:
                out = (True, self.empty_obj_recv)
        return out

    def purge(self):
        r"""Purge all messages from the comm."""
        super(CommBundle, self).purge()
        for x in self.comm_list:
            x.purge()
