import uuid
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
        icomm (dict): Response comms keyed to the ID of the associated request.
        icomm_order (list): Response comm keys in the order or the requests.
        ocomm (Comm): Request comm.

    """
    def __init__(self, name, request_comm=None, response_kwargs=None,
                 dont_open=False, **kwargs):
        if response_kwargs is None:
            response_kwargs = dict()
        ocomm_name = name
        ocomm_kwargs = kwargs
        ocomm_kwargs['direction'] = 'send'
        ocomm_kwargs['dont_open'] = True
        ocomm_kwargs['comm'] = request_comm
        self.response_kwargs = response_kwargs
        self.ocomm = get_comm(ocomm_name, **ocomm_kwargs)
        self.icomm = dict()
        self.icomm_order = []
        self.response_kwargs.setdefault('comm', self.ocomm.comm_class)
        self.response_kwargs.setdefault('recv_timeout', self.ocomm.recv_timeout)
        super(ClientComm, self).__init__(self.ocomm.name, dont_open=dont_open,
                                         recv_timeout=self.ocomm.recv_timeout,
                                         is_interface=self.ocomm.is_interface,
                                         direction='send', no_suffix=True,
                                         address=self.ocomm.address)

    @classmethod
    def is_installed(cls):
        r"""bool: Is the comm installed."""
        return get_comm_class().is_installed()

    @property
    def maxMsgSize(self):
        r"""int: Maximum size of a single message that should be sent."""
        return self.ocomm.maxMsgSize
        
    @classmethod
    def underlying_comm_class(self):
        r"""str: Name of underlying communication class."""
        return get_comm_class().underlying_comm_class()

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
            oargs, kwargs = ocomm_class.new_comm_kwargs(name, **kwargs)
        kwargs['request_comm'] = request_comm
        return args, kwargs

    @property
    def opp_comms(self):
        r"""dict: Name/address pairs for opposite comms."""
        out = super(ClientComm, self).opp_comms
        out.update(**self.ocomm.opp_comms)
        return out

    def opp_comm_kwargs(self):
        r"""Get keyword arguments to initialize communication with opposite
        comm object.

        Returns:
            dict: Keyword arguments for opposite comm object.

        """
        kwargs = super(ClientComm, self).opp_comm_kwargs()
        kwargs['comm'] = "ServerComm"
        kwargs['request_comm'] = self.ocomm.comm_class
        kwargs['response_kwargs'] = self.response_kwargs
        return kwargs
        
    def open(self):
        r"""Open the connection."""
        super(ClientComm, self).open()
        self.ocomm.open()

    def close(self, *args, **kwargs):
        r"""Close the connection."""
        self.ocomm.close(*args, **kwargs)
        for k in self.icomm_order:
            self.icomm[k].close()
        super(ClientComm, self).close(*args, **kwargs)

    @property
    def is_open(self):
        r"""bool: True if the connection is open."""
        return self.ocomm.is_open

    @property
    def is_closed(self):
        r"""bool: True if the connection is closed."""
        return self.ocomm.is_closed

    @property
    def n_msg_send(self):
        r"""int: The number of messages in the connection."""
        return self.ocomm.n_msg_send

    @property
    def n_msg_send_drain(self):
        r"""int: The number of outgoing messages in the connection to drain."""
        return self.ocomm.n_msg_send_drain

    # RESPONSE COMM
    def create_response_comm(self):
        r"""Create a response comm based on information from the last header."""
        comm_kwargs = dict(direction='recv', is_response_client=True,
                           single_use=True, **self.response_kwargs)
        header = dict(request_id=str(uuid.uuid4()))
        if header['request_id'] in self.icomm:  # pragma: debug
            raise ValueError("Request ID %s already in use." % header['request_id'])
        c = new_comm('client_response_comm.' + header['request_id'], **comm_kwargs)
        header['response_address'] = c.address
        self.icomm[header['request_id']] = c
        self.icomm_order.append(header['request_id'])
        return header

    def remove_response_comm(self):
        r"""Remove response comm."""
        key = self.icomm_order.pop(0)
        icomm = self.icomm.pop(key)
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
        msg = args[0]
        # if self.is_closed:
        #     self.debug("send(): Connection closed.")
        #     return False
        if msg != self.eof_msg:
            kwargs['header_kwargs'] = self.create_response_comm()
        out = self.ocomm.send(*args, **kwargs)
        if (not out) and (msg != self.eof_msg):
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
        # if self.is_closed:
        #     self.debug("recv(): Connection closed.")
        #     return (False, None)
        if len(self.icomm) == 0:  # pragma: debug
            raise RuntimeError("There are not any registered response comms.")
        out = self.icomm[self.icomm_order[0]].recv(*args, **kwargs)
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
        if not flag:  # pragma: debug
            return (False, self.empty_msg)
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
    
    def drain_messages(self, direction='send', **kwargs):
        r"""Sleep while waiting for messages to be drained."""
        if direction == 'send':
            self.ocomm.drain_messages(direction='send', **kwargs)

    # def purge(self):
    #     r"""Purge input and output comms."""
    #     self.ocomm.purge()
    #     # Unsure if client should purge all input comms...
    #     # for k in self.icomm_order:
    #     #     self.icomm[k].purge()
    #     super(ClientComm, self).purge()
