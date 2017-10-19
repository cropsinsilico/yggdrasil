import os
from cis_interface.communication import CommBase, get_comm, get_comm_class


_rpc_address_split = '_FROM_RPC_TO_'


class RPCComm(CommBase.CommBase):
    r"""Class for handling RPC I/O.

    Args:
        name (str): The environment variable where communication address is
            stored.
        icomm_kwargs (dict, optional): Keyword arguments for the input comm.
            Defaults to empty dict.
        ocomm_kwargs (dict, optional): Keyword arguments for the output comm.
            Defaults to empty dict.
        reverse_names (bool, optional): If True, the suffixes added to
            to name to create icomm_name and ocomm_name are reversed.
            Defaults to False.
        **kwargs: Additional keywords arguments are passed to parent class.

    Attributes:
        icomm (Comm): Input comm.
        ocomm (Comm): Output comm.

    """
    def __init__(self, name, icomm_kwargs=None, ocomm_kwargs=None,
                 dont_open=False, reverse_names=False, **kwargs):
        if icomm_kwargs is None:
            icomm_kwargs = dict()
        if ocomm_kwargs is None:
            ocomm_kwargs = dict()
        if reverse_names:
            icomm_name = icomm_kwargs.pop('name', name + '_OUT')
            ocomm_name = ocomm_kwargs.pop('name', name + '_IN')
        else:
            icomm_name = icomm_kwargs.pop('name', name + '_IN')
            ocomm_name = ocomm_kwargs.pop('name', name + '_OUT')
        icomm_kwargs['direction'] = 'recv'
        ocomm_kwargs['direction'] = 'send'
        icomm_kwargs['dont_open'] = True
        ocomm_kwargs['dont_open'] = True
        if name in os.environ or 'address' in kwargs:
            super(RPCComm, self).__init__(name, dont_open=True, **kwargs)
            icomm_kwargs.setdefault(
                'address', self.address.split(_rpc_address_split)[0])
            ocomm_kwargs.setdefault(
                'address', self.address.split(_rpc_address_split)[1])
            self.icomm = get_comm(icomm_name, **icomm_kwargs)
            self.ocomm = get_comm(ocomm_name, **ocomm_kwargs)
        else:
            self.icomm = get_comm(icomm_name, **icomm_kwargs)
            self.ocomm = get_comm(ocomm_name, **ocomm_kwargs)
            kwargs.setdefault('address', _rpc_address_split.join(
                [self.icomm.address, self.ocomm.address]))
            super(RPCComm, self).__init__(name, dont_open=True, **kwargs)
        self.icomm.recv_timeout = self.recv_timeout
        self.ocomm.recv_timeout = self.recv_timeout
        if not dont_open:
            self.open()

    @classmethod
    def comm_count(cls):
        r"""int: Number of communication connections."""
        return get_comm_class().comm_count()

    @classmethod
    def new_comm_kwargs(cls, name, icomm_name=None, ocomm_name=None,
                        icomm_comm=None, ocomm_comm=None,
                        icomm_kwargs=None, ocomm_kwargs=None,
                        reverse_names=False, **kwargs):
        r"""Initialize communication with new comms.

        Args:
            name (str): Name for new comm.
            icomm_name (str, optional): Name for new input comm. Defaults to
                name + '_IN'. This will be overriden if 'name' is in
                icomm_kwargs.
            ocomm_name (str, optional): Name for new output comm. Defaults to
                name + '_OUT'. This will be overriden if 'name' is in
                ocomm_kwargs.
            icomm_comm (str, optional): Name of class for new input comm.
                Defaults to None. This will be overrriden if 'comm' is in
                icomm_kwargs.
            ocomm_comm (str, optional): Name of class for new output comm.
                Defaults to None. This will be overrriden if 'comm' is in
                ocomm_kwargs.
            icomm_kwargs (dict, optional): Keyword arguments for the icomm_comm
                new_comm_kwargs class method.
            ocomm_kwargs (dict, optional): Keyword arguments for the ocomm_comm
                new_comm_kwargs class method.
            reverse_names (bool, optional): If True, the suffixes added to
                to name to create icomm_name and ocomm_name are reversed.
                Defaults to False.

        """
        args = [name]
        if icomm_kwargs is None:
            icomm_kwargs = dict()
        if ocomm_kwargs is None:
            ocomm_kwargs = dict()
        if icomm_name is None:
            if reverse_names:
                icomm_name = name + '_OUT'
            else:
                icomm_name = name + '_IN'
        if ocomm_name is None:
            if reverse_names:
                ocomm_name = name + '_IN'
            else:
                ocomm_name = name + '_OUT'
        icomm_name = icomm_kwargs.pop('name', icomm_name)
        ocomm_name = ocomm_kwargs.pop('name', ocomm_name)
        icomm_comm = icomm_kwargs.pop('comm', icomm_comm)
        ocomm_comm = ocomm_kwargs.pop('comm', ocomm_comm)
        icomm_class = get_comm_class(icomm_comm)
        ocomm_class = get_comm_class(ocomm_comm)
        icomm_kwargs['direction'] = 'recv'
        ocomm_kwargs['direction'] = 'send'
        ikwargs = dict(**icomm_kwargs)
        okwargs = dict(**ocomm_kwargs)
        if 'address' not in kwargs:
            if 'address' not in icomm_kwargs:
                iargs, ikwargs = icomm_class.new_comm_kwargs(icomm_name,
                                                             **icomm_kwargs)
            if 'address' not in ocomm_kwargs:
                oargs, okwargs = ocomm_class.new_comm_kwargs(ocomm_name,
                                                             **ocomm_kwargs)
        else:
            ikwargs['address'], okwargs['address'] = kwargs['address'].split(
                _rpc_address_split)
        ikwargs['name'] = icomm_name
        okwargs['name'] = ocomm_name
        ikwargs['comm'] = icomm_comm
        okwargs['comm'] = ocomm_comm
        kwargs['icomm_kwargs'] = ikwargs
        kwargs['ocomm_kwargs'] = okwargs
        return args, kwargs

    @property
    def opp_address(self):
        r"""str: Address for opposite RPC comm."""
        adds = self.address.split(_rpc_address_split)
        return _rpc_address_split.join([adds[1], adds[0]])

    def open(self):
        r"""Open the connection."""
        self.icomm.open()
        self.ocomm.open()

    def close(self):
        r"""Close the connection."""
        self.icomm.close()
        self.ocomm.close()

    @property
    def is_open(self):
        r"""bool: True if the connection is open."""
        return self.icomm.is_open and self.ocomm.is_open

    @property
    def is_closed(self):
        r"""bool: True if the connection is closed."""
        return self.icomm.is_closed and self.ocomm.is_closed

    @property
    def n_msg(self):
        r"""int: The number of messages in the connection."""
        return self.icomm.n_msg

    # SEND METHODS
    def send(self, *args, **kwargs):
        r"""Send a message to the output comm.

        Args:
            *args: Arguments are passed to output comm send method.
            **kwargs: Keyword arguments are passed to output comm send method.

        Returns:
            obj: Output from output comm send method.

        """
        return self.ocomm.send(*args, **kwargs)

    # RECV METHODS
    def recv(self, *args, **kwargs):
        r"""Receive a message from the input comm.

        Args:
            *args: Arguments are passed to input comm recv method.
            **kwargs: Keyword arguments are passed to input comm recv method.

        Returns:
            obj: Output from input comm recv method.

        """
        return self.icomm.recv(*args, **kwargs)

    # CALL
    def call(self, *args, **kwargs):
        r"""Do RPC call. The request message is sent to the output comm and the
        response is received from the input comm.

        Args:
            *args: Arguments are passed to output comm send method.
            **kwargs: Keyword arguments are passed to output comm send method

        Returns:
            obj: Output from input comm recv method.

        """
        flag = self.send(*args, **kwargs)
        if not flag:
            return (False, '')
        return self.recv(timeout=False)

    def call_nolimit(self, *args, **kwargs):
        r"""Alias for call."""
        return self.call(*args, **kwargs)
