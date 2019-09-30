from yggdrasil.communication import CommBase, get_comm
from yggdrasil.communication.ForkComm import get_comm_name
# , _address_sep
from yggdrasil.components import import_component


class CompComm(CommBase.CommBase):
    r"""Class for receiving/sending composite messages from/to multiple comms.

    Args:
        name (str): The environment variable where communication address is
            stored.
        comm (list, optional): The list of options for the comms that
            should be bundled. If not provided, the bundle will be empty.
        **kwargs: Additional keyword arguments are passed to the parent class.

    Attributes:
        comm_list (list): Comms included in this fork.

    """

    _dont_register = True
    
    def __init__(self, name, comm=None, **kwargs):
        self.comm_list = []
        self.recv_backlog = []
        address = kwargs.pop('address', None)
        if (comm in [None, 'CompComm']):
            if isinstance(address, list):
                ncomm = len(address)
            else:
                ncomm = 0
            comm = [None for i in range(ncomm)]
        assert(isinstance(comm, list))
        ncomm = len(comm)
        for i in range(ncomm):
            if comm[i] is None:
                comm[i] = {}
            if comm[i].get('name', None) is None:
                comm[i]['name'] = get_comm_name(name, i)
        if isinstance(address, list):
            assert(len(address) == ncomm)
            for i in range(ncomm):
                comm[i]['address'] = address[i]
        for i in range(ncomm):
            ikw = dict(**kwargs)
            ikw.update(**comm[i])
            iname = ikw.pop('name')
            self.comm_list.append(get_comm(iname, **ikw))
            self.recv_backlog.append([])
        if ncomm > 0:
            kwargs['address'] = [x.address for x in self.comm_list]
        kwargs['comm'] = 'CompComm'
        super(CompComm, self).__init__(name, **kwargs)
        assert(not self.single_use)
        assert(not self.is_server)
        assert(not self.is_client)

    def printStatus(self, nindent=0):
        r"""Print status of the communicator."""
        super(CompComm, self).printStatus(nindent=nindent)
        for x, fields in zip(self.comm_list, self.comm_fields):
            extra_lines = ['%-15s: %s' % ('fields', fields)]
            x.printStatus(nindent=nindent + 1, extra_lines=extra_lines)

    def __len__(self):
        return len(self.comm_list)

    @property
    def maxMsgSize(self):
        r"""int: Maximum size of a single message that should be sent."""
        return min([x.maxMsgSize for x in self.comm_list])

    @classmethod
    def new_comm_kwargs(cls, name, *args, **kwargs):
        r"""Get keyword arguments for new comm."""
        if 'address' not in kwargs:
            addresses = []
            comm = kwargs.get('comm', None)
            ncomm = kwargs.pop('ncomm', 0)
            if comm is None:
                comm = [None for i in range(ncomm)]
            assert(isinstance(comm, list))
            ncomm = len(comm)
            for i in range(ncomm):
                x = comm[i]
                if x is None:
                    x = {}
                iname = x.pop('name', get_comm_name(name, i))
                icls = import_component('comm', x.get('comm', None))
                _, ickw = icls.new_comm_kwargs(iname, **x)
                ickw['name'] = iname
                comm[i] = ickw
                addresses.append(ickw['address'])
            kwargs['comm'] = comm
            kwargs['address'] = addresses
        args = tuple([name] + list(args))
        return args, kwargs

    @property
    def opp_comms(self):
        r"""dict: Name/address pairs for opposite comms."""
        out = super(CompComm, self).opp_comms
        out.pop(self.name)
        for x in self.comm_list:
            out.update(**x.opp_comms)
        return out

    def opp_comm_kwargs(self):
        r"""Get keyword arguments to initialize communication with opposite
        comm object.

        Returns:
            dict: Keyword arguments for opposite comm object.

        """
        kwargs = super(CompComm, self).opp_comm_kwargs()
        kwargs['comm'] = [x.opp_comm_kwargs() for x in self.comm_list]
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

    def close_in_thread(self, *args, **kwargs):  # pragma: debug
        r"""In a new thread, close the comm when it is empty."""
        # for x in self.comm_list:
        #     x.close_in_thread(*args, **kwargs)
        raise Exception("CompComm should not be closed in thread.")

    @property
    def is_open(self):
        r"""bool: True if the connection is open."""
        for x in self.comm_list:
            if not x.is_open:
                return False
        return True

    @property
    def is_confirmed_send(self):
        r"""bool: True if all sent messages have been confirmed."""
        for x in self.comm_list:
            if not x.is_confirmed_send:  # pragma: debug
                return False
        return True

    @property
    def is_confirmed_recv(self):
        r"""bool: True if all received messages have been confirmed."""
        for x in self.comm_list:
            if not x.is_confirmed_recv:  # pragma: debug
                return False
        return True

    def confirm_send(self, noblock=False):
        r"""Confirm that sent message was received."""
        for x in self.comm_list:
            if not x.confirm_send(noblock=noblock):  # pragma: debug
                return False
        return True

    def confirm_recv(self, noblock=False):
        r"""Confirm that message was received."""
        for x in self.comm_list:
            if not x.confirm_recv(noblock=noblock):  # pragma: debug
                return False
        return True

    @property
    def n_msg_recv(self):
        r"""int: The number of incoming messages in the connection."""
        return max([x.n_msg_recv for x in self.comm_list])

    @property
    def n_msg_send(self):
        r"""int: The number of outgoing messages in the connection."""
        return max([x.n_msg_send for x in self.comm_list])

    @property
    def n_msg_recv_drain(self):
        r"""int: The number of incoming messages in the connection to drain."""
        return max([x.n_msg_recv_drain for x in self.comm_list])

    @property
    def n_msg_send_drain(self):
        r"""int: The number of outgoing messages in the connection to drain."""
        return max([x.n_msg_send_drain for x in self.comm_list])

    def send(self, *args, **kwargs):
        r"""Send a message.

        Args:
            *args: All arguments are assumed to be part of the message.
            **kwargs: All keywords arguments are passed to comm _send method.

        Returns:
            bool: Success or failure of send.

        """
        if (len(args) == 1) and self.is_eof(args[0]):
            args = tuple([(x.eof_msg, ) for x in self.comm_list])
        assert(len(args) == len(self))
        for x, iargs in zip(self.comm_list, args):
            out = x.send(*iargs, **kwargs)
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
        T = self.start_timeout(timeout, key_suffix='recv:forkd')
        all_out = False
        out = [(False, None) for _ in range(len(self))]
        from_backlog = [False for _ in range(len(self))]
        while ((not T.is_out) or first_comm) and self.is_open and (not all_out):
            for i in range(len(self)):
                if out[i][1] is None:
                    if self.recv_backlog[i]:
                        out[i] = self.recv_backlog[i].pop(0)
                        from_backlog[i] = True
                    else:
                        x = self.comm_list[i]
                        if x.is_open:
                            flag, msg = x.recv(*args, **kwargs)
                            if x.is_eof(msg) or (not x.is_empty_recv(msg)):
                                out[i] = (flag, msg)
            first_comm = False
            all_out = all([x is not None for x in out])
            if not all_out:
                self.sleep()
        self.stop_timeout(key_suffix='recv:forkd')
        if any([x is None for x in out]):
            # Put unused messages in backlog
            for i in range(len(self)):
                if from_backlog[i]:
                    self.recv_backlog[i].insert(0, out[i])
                else:
                    self.recv_backlog[i].append(out[i])
            if self.is_closed:
                self.debug('Comm closed')
                out = (False, None)
            else:
                out = (True, self.empty_obj_recv)
        else:
            is_eof = [x.is_eof(out[i][1]) for i, x in enumerate(self.comm_list)]
            if any(is_eof):
                if not all(is_eof):  # pragma: debug
                    raise RuntimeError("EOF not received from all comms.")
                out = (self.on_recv_eof(), self.eof_msg)
            else:
                out = (True, [x[1] for x in out])
        return out

    def purge(self):
        r"""Purge all messages from the comm."""
        super(CompComm, self).purge()
        for x in self.comm_list:
            x.purge()
