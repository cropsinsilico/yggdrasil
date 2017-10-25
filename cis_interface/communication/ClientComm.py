from cis_interface.communication import (
    CommBase, new_comm, get_comm, get_comm_class)


class ClientComm(CommBase.CommBase):
    r"""Class for handling Client side communication.

    Args:
        name (str): The environment variable where communication address is
            stored.
        request_comm (str, optional): Comm class that should be used for the
            request comm. Defaults to None.
        response_kwargs (dict, optional): Keyword arguments for the response
            comm. Defaults to empty dict.
        **kwargs: Additional keywords arguments are passed to the output comm.

    Attributes:
        response_kwargs (dict): Keyword arguments for the response comm.
        icomm (list): Response comms in the order of the sent requests.
        ocomm (Comm): Request comm.

    """
    def __init__(self, name, request_comm=None, response_kwargs=None,
                 dont_open=False, **kwargs):
        if response_kwargs is None:
            response_kwargs = dict()
        ocomm_name = name + '_OUT'
        ocomm_kwargs = kwargs
        ocomm_kwargs['direction'] = 'send'
        ocomm_kwargs['dont_open'] = True
        ocomm_kwargs['comm'] = request_comm
        self.response_kwargs = response_kwargs
        self.ocomm = get_comm(ocomm_name, **ocomm_kwargs)
        self.icomm = []
        self.response_kwargs.setdefault('comm', self.ocomm.comm_class)
        super(ClientComm, self).__init__(name, dont_open=dont_open,
                                         address=self.ocomm.address)

    @classmethod
    def comm_count(cls):
        r"""int: Number of communication connections."""
        return get_comm_class().comm_count()

    @classmethod
    def new_comm_kwargs(cls, name, request_comm=None, **kwargs):
        r"""Initialize communication with new comms.

        Args:
            name (str): Name for new comm.
            request_comm (str, optional): Name of class for new output comm.
                Defaults to None.

        """
        args = [name]
        ocomm_class = get_comm_class(request_comm)
        kwargs['direction'] = 'send'
        if 'address' not in kwargs:
            oargs, kwargs = ocomm_class.new_comm_kwargs(name + '_OUT',
                                                        **kwargs)
        kwargs['request_comm'] = request_comm
        return args, kwargs

    def opp_comm_kwargs(self):
        r"""Get keyword arguments to initialize communication with opposite
        comm object.

        Returns:
            dict: Keyword arguments for opposite comm object.

        """
        kwargs = super(ClientComm, self).opp_comm_kwargs()
        kwargs['comm'] = get_comm_class("ServerComm")
        kwargs['request_comm'] = self.ocomm.comm_class
        kwargs['response_kwargs'] = self.response_kwargs
        return kwargs
        
    def open(self):
        r"""Open the connection."""
        super(ClientComm, self).open()
        self.ocomm.open()

    def close(self):
        r"""Close the connection."""
        self.ocomm.close()
        for icomm in self.icomm:
            icomm.close()
        super(ClientComm, self).close()

    @property
    def is_open(self):
        r"""bool: True if the connection is open."""
        return self.ocomm.is_open

    @property
    def is_closed(self):
        r"""bool: True if the connection is closed."""
        return self.ocomm.is_closed

    @property
    def n_msg(self):
        r"""int: The number of messages in the connection."""
        return self.ocomm.n_msg

    # RESPONSE COMM
    def create_response_comm(self):
        r"""Create a response comm based on information from the last header."""
        comm_kwargs = dict(direction='recv', **self.response_kwargs)
        self.icomm.append(new_comm(self.name + '.client_response_comm',
                                   **comm_kwargs))

    def remove_response_comm(self):
        r"""Remove response comm."""
        icomm = self.icomm.pop(0)
        icomm.close()

    # SEND METHODS
    def send(self, *args, **kwargs):
        r"""Create a response comm and then send a message to the output comm
        with the response address in the header.

        Args:
            *args: Arguments are passed to output comm send method.
            **kwargs: Keyword arguments are passed to output comm send method.

        Returns:
            obj: Output from output comm send method.

        """
        self.create_response_comm()
        kwargs['send_header'] = True
        kwargs['header_kwargs'] = dict(response_address=self.icomm[-1].address)
        out = self.ocomm.send(*args, **kwargs)
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
        if len(self.icomm) == 0:
            raise RuntimeError("There are not any registered response comms.")
        out = self.icomm[0].recv(*args, **kwargs)
        self.remove_response_comm()
        return out

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

    # OLD STYLE ALIASES
    def rpcSend(self, *args, **kwargs):
        r"""Alias for RPCComm.send"""
        return self.send(*args, **kwargs)

    def rpcRecv(self, *args, **kwargs):
        r"""Alias for RPCComm.recv"""
        return self.recv(*args, **kwargs)
    
    def rpcCall(self, *args, **kwargs):
        r"""Alias for RPCComm.call"""
        return self.call(*args, **kwargs)
    
    def purge(self):
        r"""Purge input and output comms."""
        self.ocomm.purge()
        if self.icomm is not None:
            self.icomm.purge()
        super(ClientComm, self).purge()
