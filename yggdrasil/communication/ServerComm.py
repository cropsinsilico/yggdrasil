import os
import uuid
from collections import OrderedDict
from yggdrasil.communication import CommBase, get_comm, import_comm
from yggdrasil.drivers.RPCRequestDriver import YGG_CLIENT_EOF


class ServerComm(CommBase.CommBase):
    r"""Class for handling Server side communication.

    Args:
        name (str): The environment variable where communication address is
            stored.
        request_commtype (str, optional): Comm class that should be used for
            the request comm. Defaults to None.
        response_kwargs (dict, optional): Keyword arguments for the response
            comm. Defaults to empty dict.
        **kwargs: Additional keywords arguments are passed to the input comm.

    Attributes:
        response_kwargs (dict): Keyword arguments for the response comm.
        icomm (Comm): Request comm.
        ocomm (OrderedDict): Response comms for each request.

    """

    _commtype = 'server'
    _dont_register = True
    
    def __init__(self, name, request_commtype=None, response_kwargs=None,
                 **kwargs):
        if response_kwargs is None:
            response_kwargs = dict()
        self.icomm_name = name
        self.icomm_kwargs = kwargs
        self.response_kwargs = response_kwargs
        self.request_commtype = request_commtype
        self.icomm = None
        self.ocomm = OrderedDict()
        self._used_response_comms = dict()
        self.clients = []
        self.closed_clients = []
        self.nclients_expected = int(os.environ.get('YGG_NCLIENTS', 0))
        kwargs_base = {k: kwargs[k] for k in
                       ['recv_timeout', 'is_interface', 'is_async', 'address',
                        'direct_connection', 'dont_open', 'no_suffix',
                        'reverse_names']
                       if k in kwargs}
        super(ServerComm, self).__init__(name, direction='recv',
                                         **kwargs_base)

    def _init_before_open(self, **kwargs):
        r"""Initialization steps that should be performed after base class, but
        before the comm is opened."""
        super(ServerComm, self)._init_before_open(**kwargs)
        self.icomm_kwargs.update(direction='recv',
                                 dont_open=True,
                                 commtype=self.request_commtype)
        self.icomm_kwargs.setdefault('is_server', True)
        self.icomm_kwargs.setdefault('direct_connection',
                                     self.direct_connection)
        self.icomm_kwargs.setdefault('use_async',
                                     self.icomm_kwargs.pop('is_async', False))
        if self.icomm_kwargs.get('use_async', False):
            self.icomm_kwargs.setdefault('async_recv_method', 'recv_message')
        self.icomm = get_comm(self.icomm_name, **self.icomm_kwargs)
        self.response_kwargs.setdefault('commtype', self.icomm._commtype)
        self.response_kwargs.setdefault('recv_timeout', self.icomm.recv_timeout)
        self.response_kwargs.setdefault('language', self.icomm.language)
        self.response_kwargs.setdefault('use_async', self.icomm.is_async)
        self.response_kwargs.setdefault('direct_connection',
                                        self.icomm.direct_connection)
        
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
        lines, prefix = super(ServerComm, self).get_status_message(
            nindent=nindent, **kwargs)
        lines.append('%s%-15s:' % (prefix, 'request comm'))
        lines += self.icomm.get_status_message(nindent=(nindent + 1))[0]
        lines.append('%s%-15s:' % (prefix, 'response comms'))
        for x in self.ocomm.values():
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
        return self.icomm.maxMsgSize
        
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
            request_commtype (str, optional): Name of class for new input
                comm. Defaults to None.

        """
        args = [name]
        icomm_class = import_comm(request_commtype)
        kwargs['direction'] = 'recv'
        if 'address' not in kwargs:
            iargs, kwargs = icomm_class.new_comm_kwargs(name, **kwargs)
        kwargs['request_commtype'] = request_commtype
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
        kwargs['commtype'] = "client"
        kwargs['request_commtype'] = self.icomm._commtype
        kwargs['response_kwargs'] = self.response_kwargs
        kwargs['direct_connection'] = self.direct_connection
        return kwargs
        
    def open(self):
        r"""Open the connection."""
        super(ServerComm, self).open()
        self.icomm.open()

    def close(self, *args, **kwargs):
        r"""Close the connection."""
        self.icomm.close(*args, **kwargs)
        for ocomm in self.ocomm.values():
            ocomm.close()
        for ocomm in self._used_response_comms.values():
            ocomm.close()
        super(ServerComm, self).close(*args, **kwargs)

    @property
    def is_open(self):
        r"""bool: True if the connection is open."""
        return self.icomm.is_open

    @property
    def is_closed(self):
        r"""bool: True if the connection is closed."""
        return self.icomm.is_closed

    @property
    def n_msg_recv(self):
        r"""int: The number of messages in the connection."""
        return self.icomm.n_msg_recv

    @property
    def n_msg_recv_drain(self):
        r"""int: The number of messages in the connection to drain."""
        return self.icomm.n_msg_recv_drain

    @property
    def open_clients(self):
        r"""list: Available open clients."""
        return list(set(self.clients) - set(self.closed_clients))

    @property
    def all_clients_connected(self):
        r"""bool: True if all expected clients have connected.
        False otherwise."""
        return ((self.nclients_expected > 0)
                and (len(self.clients) >= self.nclients_expected))

    # RESPONSE COMM
    def create_response_comm(self, header):
        r"""Create a response comm based on information from the last header."""
        if not isinstance(header, dict):  # pragma: debug
            raise RuntimeError("No header received with last message.")
        elif 'response_address' not in header:  # pragma: debug
            raise RuntimeError("Last header does not contain response address.")
        comm_kwargs = dict(address=header['response_address'],
                           direction='send',
                           single_use=True, **self.response_kwargs)
        if self.direct_connection:
            comm_kwargs['is_response_client'] = True
        else:
            comm_kwargs['is_response_server'] = True
        response_id = header['request_id']
        while response_id in self.ocomm:  # pragma: debug
            response_id += str(uuid.uuid4())
        header['response_id'] = response_id
        self.ocomm[response_id] = get_comm(
            self.name + '.server_response_comm.' + response_id,
            **comm_kwargs)
        client_model = header.get('model', '')
        self.ocomm[response_id].client_model = client_model
        self.ocomm[response_id].request_id = header['request_id']
        if client_model and (client_model not in self.clients):
            self.clients.append(client_model)

    def remove_response_comm(self, response_id):
        r"""Remove response comm.

        Args:
            response_id (str): The ID used to register the response
                comm that should be removed.

        """
        ocomm = self.ocomm.pop(response_id, None)
        if ocomm is not None:
            ocomm.close_in_thread(no_wait=True)
            self._used_response_comms[ocomm.name] = ocomm

    # SEND METHODS
    def send_to(self, response_id, *args, **kwargs):
        r"""Send a message to a specific response comm.

        Args:
            response_id (str): ID used to register the response comm.
            *args: Arguments are passed to output comm send method.
            **kwargs: Keyword arguments are passed to output comm send method.
    
        Returns:
            obj: Output from output comm send method.

        """
        kwargs.setdefault('header_kwargs', {})
        kwargs['header_kwargs']['response_id'] = response_id
        return self.send(*args, **kwargs)
        
    def prepare_message(self, *args, **kwargs):
        r"""Perform actions preparing to send a message.

        Args:
            *args: Components of the outgoing message.
            **kwargs: Keyword arguments are passed to the request comm's
                prepare_message method.

        Returns:
            CommMessage: Serialized and annotated message.

        """
        if len(self.ocomm) == 0:  # pragma: debug
            raise RuntimeError("There is no registered response comm.")
        kwargs.setdefault('header_kwargs', {})
        response_id = kwargs['header_kwargs'].get('response_id', None)
        if response_id is None:
            response_id = next(iter(self.ocomm.keys()))
            kwargs['header_kwargs']['response_id'] = response_id
        kwargs['header_kwargs']['request_id'] = self.ocomm[response_id].request_id
        return self.ocomm[response_id].prepare_message(*args, **kwargs)
        
    def send_message(self, msg, **kwargs):
        r"""Send a message encapsulated in a CommMessage object.

        Args:
            msg (CommMessage): Message to be sent.
            **kwargs: Additional keyword arguments are passed to the response
                comm's send_message method.

        Returns:
            bool: Success or failure of send.
        
        """
        response_id = msg.header['response_id']
        out = self.ocomm[response_id].send_message(msg, **kwargs)
        self.errors += self.ocomm[response_id].errors
        if out:
            # Don't close here on failure which will allow send to be called
            # again in async or driver loop
            self.remove_response_comm(response_id)
        return out
                                                  
    # RECV METHODS
    def recv_from(self, *args, **kwargs):
        r"""Receive a message from the input comm and open a new response comm
        for output using address from the header, returning the response_id.

        Args:
            *args: Arguments are passed to input comm recv method.
            **kwargs: Keyword arguments are passed to input comm recv method.

        Returns:
            tuple(bool, obj, str): Success or failure of recv call,
                output from input comm recv method, and response_id that
                response should be sent to.

        """
        return_message_object = kwargs.pop('return_message_object', False)
        kwargs['return_message_object'] = True
        response_id = None
        out = self.recv(*args, **kwargs)
        if not return_message_object:
            if out.flag == CommBase.FLAG_SUCCESS:
                response_id = out.header['response_id']
            out = (bool(out.flag), out.args, response_id)
        return out
    
    def recv_message(self, *args, **kwargs):
        r"""Receive a message.

        Args:
            *args: Arguments are passed to the request comm's recv_message method.
            **kwargs: Keyword arguments are passed to the request comm's recv_message
                method.

        Returns:
            CommMessage: Received message.

        """
        out = self.icomm.recv_message(*args, **kwargs)
        self.errors += self.icomm.errors
        return out
        
    def finalize_message(self, msg, **kwargs):
        r"""Perform actions to decipher a message.

        Args:
            msg (CommMessage): Initial message object to be finalized.
            **kwargs: Keyword arguments are passed to the request comm's
                finalize_message method.

        Returns:
            CommMessage: Deserialized and annotated message.

        """
        def check_for_client_info(msg):
            if msg.flag == CommBase.FLAG_SUCCESS:
                if isinstance(msg.args, bytes) and (msg.args == YGG_CLIENT_EOF):
                    self.debug("Client signed off: %s", msg.header['model'])
                    self.closed_clients.append(msg.header['model'])
                    msg.flag = CommBase.FLAG_SKIP
                else:
                    self.create_response_comm(msg.header)
            return msg
        out = self.icomm.finalize_message(msg, **kwargs)
        return check_for_client_info(out)
        
    # OLD STYLE ALIASES
    def rpcSend(self, *args, **kwargs):
        r"""Alias for RPCComm.send"""
        return self.send(*args, **kwargs)

    def rpcRecv(self, *args, **kwargs):
        r"""Alias for RPCComm.recv"""
        return self.recv(*args, **kwargs)
        
    def drain_messages(self, direction='recv', **kwargs):
        r"""Sleep while waiting for messages to be drained."""
        if direction == 'recv':
            self.icomm.drain_messages(direction='recv', **kwargs)
            self.errors += self.icomm.errors

    def purge(self):
        r"""Purge input and output comms."""
        self.icomm.purge()
        # Not sure if server should purge the response queue...
        # for ocomm in self.ocomm.values():
        #     ocomm.purge()
        super(ServerComm, self).purge()
    
    def drain_server_signon_messages(self, **kwargs):
        r"""Drain server signon messages. This should only be used
        for testing purposes."""
        self.icomm.drain_server_signon_messages(**kwargs)
