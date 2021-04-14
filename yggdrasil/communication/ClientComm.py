import uuid
from yggdrasil.communication import CommBase, new_comm, get_comm, import_comm


class ClientComm(CommBase.CommBase):
    r"""Class for handling Client side communication.

    Args:
        name (str): The environment variable where communication address is
            stored.
        request_commtype (str, optional): Comm class that should be used for
            the request comm. Defaults to None.
        response_kwargs (dict, optional): Keyword arguments for the response
            comm. Defaults to empty dict.
        **kwargs: Additional keywords arguments are passed to the output comm.

    Attributes:
        response_kwargs (dict): Keyword arguments for the response comm.
        icomm (dict): Response comms keyed to the ID of the associated request.
        icomm_order (list): Response comm keys in the order or the requests.
        ocomm (Comm): Request comm.

    """

    _commtype = 'client'
    _dont_register = True
    
    def __init__(self, name, request_commtype=None, response_kwargs=None,
                 **kwargs):
        if response_kwargs is None:
            response_kwargs = dict()
        self.ocomm_name = name
        self.ocomm_kwargs = kwargs
        self.request_commtype = request_commtype
        self.response_kwargs = response_kwargs
        self.ocomm = None
        self.icomm = dict()
        self.icomm_order = []
        kwargs_base = {k: kwargs[k] for k in
                       ['recv_timeout', 'is_interface', 'is_async', 'address',
                        'direct_connection', 'dont_open', 'no_suffix',
                        'reverse_names']
                       if k in kwargs}
        super(ClientComm, self).__init__(name, direction='send',
                                         **kwargs_base)

    def _init_before_open(self, **kwargs):
        r"""Initialization steps that should be performed after base class, but
        before the comm is opened."""
        super(ClientComm, self)._init_before_open(**kwargs)
        if self.direct_connection:
            self.ocomm_kwargs.setdefault('is_client', True)
        self.ocomm_kwargs.update(direction='send',
                                 dont_open=True,
                                 commtype=self.request_commtype)
        self.ocomm_kwargs.setdefault('direct_connection',
                                     self.direct_connection)
        self.ocomm_kwargs.setdefault('use_async',
                                     self.ocomm_kwargs.pop('is_async', False))
        self.ocomm = get_comm(self.ocomm_name, **self.ocomm_kwargs)
        self.response_kwargs.setdefault('commtype', self.ocomm._commtype)
        self.response_kwargs.setdefault('recv_timeout', self.ocomm.recv_timeout)
        self.response_kwargs.setdefault('language', self.ocomm.language)
        self.response_kwargs.setdefault('use_async', self.ocomm.is_async)
        self.response_kwargs.setdefault('direct_connection',
                                        self.ocomm.direct_connection)
        
    def get_status_message(self, nindent=0, **kwargs):
        r"""Return lines composing a status message.
        
        Args:
            nindent (int, optional): Number of tabs that should
                be used to indent each line. Defaults to 0.
            *kwargs: Additional arguments are passed to the
                parent class's method.
                
        Returns:
            tuple(list, prefix): Lines composing the status message and the
                prefix string used for the last message.

        """
        lines, prefix = super(ClientComm, self).get_status_message(
            nindent=nindent, **kwargs)
        lines.append('%s%-15s:' % (prefix, 'request comm'))
        lines += self.ocomm.get_status_message(nindent=(nindent + 1))[0]
        lines.append('%s%-15s:' % (prefix, 'response comms'))
        for x in self.icomm.values():
            lines += x.get_status_message(nindent=(nindent + 1))[0]
        return lines, prefix
    
    @classmethod
    def is_installed(cls, language=None):
        r"""Determine if the necessary libraries are installed for this
        communication class.

        Args:
            language (str, optional): Specific language that should be checked
                for compatibility. Defaults to None and all languages supported
                on the current platform will be checked.

        Returns:
            bool: Is the comm installed.

        """
        return import_comm().is_installed(language=language)

    @property
    def maxMsgSize(self):
        r"""int: Maximum size of a single message that should be sent."""
        return self.ocomm.maxMsgSize
        
    @classmethod
    def underlying_comm_class(self):
        r"""str: Name of underlying communication class."""
        return import_comm().underlying_comm_class()

    @classmethod
    def comm_count(cls):
        r"""int: Number of communication connections."""
        return import_comm().comm_count()

    @classmethod
    def new_comm_kwargs(cls, name, request_commtype=None, **kwargs):
        r"""Initialize communication with new comms.

        Args:
            name (str): Name for new comm.
            request_commtype (str, optional): Name of class for new output
                comm. Defaults to None.

        """
        args = [name]
        ocomm_class = import_comm(request_commtype)
        kwargs['direction'] = 'send'
        if 'address' not in kwargs:
            oargs, kwargs = ocomm_class.new_comm_kwargs(name, **kwargs)
        kwargs['request_commtype'] = request_commtype
        return args, kwargs

    @property
    def opp_address(self):
        r"""str: Address for opposite comm."""
        return self.ocomm.opp_address
        
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
        kwargs['commtype'] = "server"
        kwargs['request_commtype'] = self.ocomm._commtype
        kwargs['response_kwargs'] = self.response_kwargs
        kwargs['direct_connection'] = self.direct_connection
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

    def atexit(self):  # pragma: debug
        r"""Close operations."""
        if self.ocomm:
            self.send_eof()
            self.ocomm.atexit()
        super(ClientComm, self).atexit()
        
    # RESPONSE COMM
    def create_response_comm(self):
        r"""Create a response comm based on information from the last header."""
        comm_kwargs = dict(direction='recv', is_response_client=True,
                           single_use=True, **self.response_kwargs)
        if comm_kwargs.get('use_async', False):
            comm_kwargs['async_recv_method'] = 'recv_message'
        header = dict(request_id=str(uuid.uuid4()))
        while header['request_id'] in self.icomm:  # pragma: debug
            header['request_id'] += str(uuid.uuid4())
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
    def prepare_message(self, *args, **kwargs):
        r"""Perform actions preparing to send a message.

        Args:
            *args: Components of the outgoing message.
            **kwargs: Keyword arguments are passed to the request comm's
                prepare_message method.

        Returns:
            CommMessage: Serialized and annotated message.

        """
        def add_response_address(msg):
            if msg.flag == CommBase.FLAG_SUCCESS:
                if msg.header is None:
                    msg.header = {}
                msg.header.update(self.create_response_comm())
            return msg
        kwargs.setdefault('after_prepare_message', [])
        kwargs['after_prepare_message'].append(add_response_address)
        return self.ocomm.prepare_message(*args, **kwargs)
        
    def send_message(self, msg, **kwargs):
        r"""Send a message encapsulated in a CommMessage object.

        Args:
            msg (CommMessage): Message to be sent.
            **kwargs: Additional keyword arguments are passed to the request
                comm's send_message method.

        Returns:
            bool: Success or failure of send.
        
        """
        out = self.ocomm.send_message(msg, **kwargs)
        self.errors += self.ocomm.errors
        return out
        
    # RECV METHODS
    def recv_message(self, *args, **kwargs):
        r"""Receive a message.

        Args:
            *args: Arguments are passed to the response comm's recv_message method.
            **kwargs: Keyword arguments are passed to the response comm's recv_message
                method.

        Returns:
            CommMessage: Received message.

        """
        if len(self.icomm) == 0:  # pragma: debug
            raise RuntimeError("There are not any registered response comms.")
        out = self.icomm[self.icomm_order[0]].recv_message(*args, **kwargs)
        self.errors += self.icomm[self.icomm_order[0]].errors
        return out

    def finalize_message(self, msg, **kwargs):
        r"""Perform actions to decipher a message.

        Args:
            msg (CommMessage): Initial message object to be finalized.
            **kwargs: Keyword arguments are passed to the response comm's
                finalize_message method.

        Returns:
            CommMessage: Deserialized and annotated message.

        """
        if len(self.icomm) == 0:  # pragma: debug
            raise RuntimeError("There are not any registered response comms.")
        msg = self.icomm[self.icomm_order[0]].finalize_message(msg, **kwargs)
        if msg.flag in [CommBase.FLAG_SUCCESS, CommBase.FLAG_FAILURE]:
            self.remove_response_comm()
        return msg
        
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
            return (False, self.empty_obj_recv)
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
