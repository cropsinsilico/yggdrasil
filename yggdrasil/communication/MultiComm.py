from yggdrasil.communication import CommBase, get_comm
from yggdrasil.components import import_component


_address_sep = ':YGG_ADD:'


class MultiComm(CommBase.CommBase):
    r"""Class for receiving/sending messages from/to multiple comms.

    Args:
        name (str): The environment variable where communication address is
            stored.
        comm (list, optional): The list of options for the comms that
            should be bundled. If not provided, the bundle will be empty.
        **kwargs: Additional keyword arguments are passed to the parent class.

    Attributes:
        comm_list (list): Comms included in this multi.
        curr_comm_index (int): Index comm that next receive will be from.

    """

    _dont_register = True
    _schema_properties = {'composite': {'type': 'boolean', 'default': False}}
                          
    def __init__(self, name, comm=None, **kwargs):
        keys_per_comm = ['address']
        keys_not_comm = ['composite', 'language', 'filter',
                         'recv_converter', 'send_converter']
        if kwargs.get('composite', False):
            keys_per_comm += ['field_names', 'field_units']
            keys_not_comm += ['serializer', 'format_str']
        else:
            keys_per_comm += []
            keys_not_comm += []
        self.comm_list = []
        self.curr_comm_index = 0
        if (comm is None) or isinstance(comm, str):
            if isinstance(kwargs.get('address', None), list):
                ncomm = len(kwargs['address'])
            else:
                ncomm = 0
            comm = [None for i in range(ncomm)]
        assert(isinstance(comm, list))
        ncomm = len(comm)
        for i in range(ncomm):
            if comm[i] is None:
                comm[i] = {}
            if comm[i].get('name', None) is None:
                comm[i]['name'] = self.get_comm_name(name, i)
        for k in keys_per_comm:
            iobj = kwargs.pop(k, None)
            if isinstance(iobj, list):
                assert(len(iobj) == ncomm)
                for i in range(ncomm):
                    comm[i][k] = iobj[i]
                    if (k in ['field_names', 'field_units']) and isinstance(iobj[i], str):
                        comm[i][k] = [comm[i][k]]
            elif iobj is not None:  # pragma: debug
                raise RuntimeError("Keyword %s is not a list." % k)
        top_kwargs = {}
        for k in keys_not_comm:
            if k in kwargs:
                top_kwargs[k] = kwargs.pop(k)
        for i in range(ncomm):
            ikw = dict(**kwargs)
            ikw.update(**comm[i])
            iname = ikw.pop('name')
            self.comm_list.append(get_comm(iname, **ikw))
        if ncomm > 0:
            kwargs['address'] = [x.address for x in self.comm_list]
        kwargs['comm'] = self.comm_class
        kwargs.update(top_kwargs)
        super(MultiComm, self).__init__(name, **kwargs)
        assert(not self.single_use)
        assert(not self.is_server)
        assert(not self.is_client)

    @classmethod
    def get_comm_name(cls, name, i):
        r"""Get the name of the ith comm in the series.

        Args:
            name (str): Name of the fork comm.
            i (int): Index of comm in fork bundle.

        Returns:
            str: Name of ith comm in fork bundle.

        """
        return '%s_%d' % (name, i)

    def printStatus(self, nindent=0):
        r"""Print status of the communicator."""
        super(MultiComm, self).printStatus(nindent=nindent)
        for x in self.comm_list:
            x.printStatus(nindent=nindent + 1)

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
                iname = x.pop('name', cls.get_comm_name(name, i))
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
        out = super(MultiComm, self).opp_comms
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
        kwargs = super(MultiComm, self).opp_comm_kwargs()
        kwargs['comm'] = [x.opp_comm_kwargs() for x in self.comm_list]
        kwargs['composite'] = self.composite
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
        raise Exception("MultiComm should not be closed in thread.")

    @property
    def is_open(self):
        r"""bool: True if the connection is open."""
        raise NotImplementedError  # pragma: debug

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
        raise NotImplementedError  # pragma: debug

    @property
    def n_msg_send(self):
        r"""int: The number of outgoing messages in the connection."""
        raise NotImplementedError  # pragma: debug

    @property
    def n_msg_recv_drain(self):
        r"""int: The number of incoming messages in the connection to drain."""
        raise NotImplementedError  # pragma: debug

    @property
    def n_msg_send_drain(self):
        r"""int: The number of outgoing messages in the connection to drain."""
        raise NotImplementedError  # pragma: debug

    def send_multipart(self, *args, **kwargs):
        r"""Send a message.

        Args:
            *args: All arguments are assumed to be part of the message.
            **kwargs: All keywords arguments are passed to comm _send method.

        Returns:
            bool: Success or failure of send.

        """
        raise NotImplementedError  # pragma: debug

    def recv_multipart(self, *args, **kwargs):
        r"""Receive a message.

        Args:
            *args: All arguments are passed to comm _recv method.
            **kwargs: All keywords arguments are passed to comm _recv method.

        Returns:
            tuple (bool, obj): Success or failure of receive and received
                message.

        """
        raise NotImplementedError  # pragma: debug

    def purge(self):
        r"""Purge all messages from the comm."""
        super(MultiComm, self).purge()
        for x in self.comm_list:
            x.purge()
