from cis_interface import backwards
from cis_interface.communication import CommBase, get_comm, get_comm_class


class ServerComm(CommBase.CommBase):
    r"""Class for handling Server side communication.

    Args:
        name (str): The environment variable where communication address is
            stored.
        request_comm (str, optional): Comm class that should be used for the
            request comm. Defaults to None.
        response_kwargs (dict, optional): Keyword arguments for the response
            comm. Defaults to empty dict.
        reverse_names (bool, optional): If True, the suffix added to
            name to create icomm_name are reversed. Defaults to False.
        **kwargs: Additional keywords arguments are passed to the input comm.

    Attributes:
        response_kwargs (dict): Keyword arguments for the response comm.
        icomm (Comm): Request comm.
        ocomm (Comm): Response comm for last request.

    """
    def __init__(self, name, request_comm=None, response_kwargs=None,
                 dont_open=False, reverse_names=False, **kwargs):
        if response_kwargs is None:
            response_kwargs = dict()
        icomm_name = name
        icomm_kwargs = kwargs
        icomm_kwargs['direction'] = 'recv'
        icomm_kwargs['reverse_names'] = reverse_names
        icomm_kwargs['dont_open'] = True
        icomm_kwargs['comm'] = request_comm
        self.response_kwargs = response_kwargs
        self.icomm = get_comm(icomm_name, **icomm_kwargs)
        self.ocomm = None
        self.response_kwargs.setdefault('comm', self.icomm.comm_class)
        self.response_kwargs.setdefault('recv_timeout', self.icomm.recv_timeout)
        super(ServerComm, self).__init__(self.icomm.name, dont_open=dont_open,
                                         recv_timeout=self.icomm.recv_timeout,
                                         direction='recv', no_suffix=True,
                                         address=self.icomm.address)

    @classmethod
    def comm_count(cls):
        r"""int: Number of communication connections."""
        return get_comm_class().comm_count()

    @classmethod
    def new_comm_kwargs(cls, name, request_comm=None, **kwargs):
        r"""Initialize communication with new comms.

        Args:
            name (str): Name for new comm.
            request_comm (str, optional): Name of class for new input comm.
                Defaults to None.

        """
        args = [name]
        icomm_class = get_comm_class(request_comm)
        kwargs['direction'] = 'recv'
        if 'address' not in kwargs:
            iargs, kwargs = icomm_class.new_comm_kwargs(name, **kwargs)
        kwargs['request_comm'] = request_comm
        return args, kwargs

    @property
    def opp_comms(self):
        r"""dict: Name/address pairs for opposite comms."""
        out = super(ServerComm, self).opp_comms
        out.update(**self.icomm.opp_comms)
        return out

    def opp_comm_kwargs(self):
        r"""Get keyword arguments to initialize communication with opposite
        comm object.

        Returns:
            dict: Keyword arguments for opposite comm object.

        """
        kwargs = super(ServerComm, self).opp_comm_kwargs()
        kwargs['comm'] = get_comm_class("ClientComm")
        kwargs['request_comm'] = self.icomm.comm_class
        kwargs['response_kwargs'] = self.response_kwargs
        return kwargs
        
    def open(self):
        r"""Open the connection."""
        super(ServerComm, self).open()
        self.icomm.open()

    def close(self):
        r"""Close the connection."""
        self.icomm.close()
        if self.ocomm is not None:
            self.ocomm.close()
        super(ServerComm, self).close()

    @property
    def is_open(self):
        r"""bool: True if the connection is open."""
        return self.icomm.is_open

    @property
    def is_closed(self):
        r"""bool: True if the connection is closed."""
        return self.icomm.is_closed

    @property
    def n_msg(self):
        r"""int: The number of messages in the connection."""
        return self.icomm.n_msg

    # RESPONSE COMM
    def create_response_comm(self):
        r"""Create a response comm based on information from the last header."""
        if not isinstance(self.icomm._last_header, dict):
            raise RuntimeError("No header received with last message.")
        elif 'response_address' not in self.icomm._last_header:
            raise RuntimeError("Last header does not contain response address.")
        comm_kwargs = dict(address=self.icomm._last_header['response_address'],
                           direction='send', **self.response_kwargs)
        self.ocomm = get_comm(self.name + '.server_response_comm',
                              **comm_kwargs)

    def remove_response_comm(self):
        r"""Remove response comm."""
        self.icomm._last_header = None
        # self.ocomm.close()
        self.ocomm = None

    # SEND METHODS
    def send(self, *args, **kwargs):
        r"""Send a message to the output comm.

        Args:
            *args: Arguments are passed to output comm send method.
            **kwargs: Keyword arguments are passed to output comm send method.

        Returns:
            obj: Output from output comm send method.

        """
        if self.ocomm is None:
            raise RuntimeError("There is no registered response comm.")
        out = self.ocomm.send(*args, **kwargs)
        self.remove_response_comm()
        return out

    # RECV METHODS
    def recv(self, *args, **kwargs):
        r"""Receive a message from the input comm and open a new response comm
        for output using address from the header.

        Args:
            *args: Arguments are passed to input comm recv method.
            **kwargs: Keyword arguments are passed to input comm recv method.

        Returns:
            obj: Output from input comm recv method.

        """
        flag, msg = self.icomm.recv(*args, **kwargs)
        if flag:
            self.create_response_comm()
        return flag, msg

    # OLD STYLE ALIASES
    def rpcSend(self, *args, **kwargs):
        r"""Alias for RPCComm.send"""
        return self.send(*args, **kwargs)

    def rpcRecv(self, *args, **kwargs):
        r"""Alias for RPCComm.recv"""
        return self.recv(*args, **kwargs)
    
    def purge(self):
        r"""Purge input and output comms."""
        self.icomm.purge()
        if self.ocomm is not None:
            self.ocomm.purge()
        super(ServerComm, self).purge()
