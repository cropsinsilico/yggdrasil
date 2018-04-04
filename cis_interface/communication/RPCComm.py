import os
import copy
from cis_interface import backwards
from cis_interface.communication import CommBase, get_comm, get_comm_class


_rpc_address_split = '_FROM_RPC_TO_'


class RPCComm(CommBase.CommBase):
    r"""Class for handling RPC I/O.

    Args:
        name (str): The environment variable where communication address is
            stored.
        address (str, optional): Communication info. Default to None and
            address is taken from the environment variable.
        comm (str, optional): The comm that should be created. This only serves
            as a check that the correct class is being created. Defaults to None.
        icomm_kwargs (dict, optional): Keyword arguments for the input comm.
            Defaults to empty dict.
        ocomm_kwargs (dict, optional): Keyword arguments for the output comm.
            Defaults to empty dict.
        dont_open (bool, optional): If True, the connection will not be opened.
            Defaults to False.
        **kwargs: Additional keywords arguments are passed to parent class as
            well as the input and output comms.

    Attributes:
        icomm (Comm): Input comm.
        ocomm (Comm): Output comm.

    """
    def __init__(self, name, address=None, comm=None,
                 icomm_kwargs=None, ocomm_kwargs=None,
                 dont_open=False, **kwargs):
        if icomm_kwargs is None:
            icomm_kwargs = dict()
        if ocomm_kwargs is None:
            ocomm_kwargs = dict()
        icomm_name = icomm_kwargs.pop('name', name)
        ocomm_name = ocomm_kwargs.pop('name', name)
        icomm_kwargs['direction'] = 'recv'
        ocomm_kwargs['direction'] = 'send'
        icomm_kwargs['dont_open'] = True
        ocomm_kwargs['dont_open'] = True
        # if comm not in [None, self.comm_class]:
        #     icomm_kwargs.setdefault('comm', comm)
        #     ocomm_kwargs.setdefault('comm', comm)
        #     comm = self.comm_class
        # Combine kwargs and icomm/ocomm specific ones
        ikwargs = copy.deepcopy(kwargs)
        okwargs = copy.deepcopy(kwargs)
        ikwargs.update(**icomm_kwargs)
        okwargs.update(**ocomm_kwargs)
        kwargs['no_suffix'] = True
        if (name in os.environ) or (address is not None):
            super(RPCComm, self).__init__(name, address=address, comm=comm,
                                          dont_open=True,
                                          **kwargs)
            ikwargs.setdefault(
                'address', self.address.split(_rpc_address_split)[0])
            okwargs.setdefault(
                'address', self.address.split(_rpc_address_split)[1])
            self._setup_comms(icomm_name, ikwargs,
                              ocomm_name, okwargs)
        else:
            self._setup_comms(icomm_name, ikwargs,
                              ocomm_name, okwargs)
            if address is None:
                address = _rpc_address_split.join(
                    [self.icomm.address, self.ocomm.address])
            # Close before raising the error
            try:
                super(RPCComm, self).__init__(name, address=address, comm=comm,
                                              dont_open=True,
                                              **kwargs)
            except BaseException as e:
                self.close(skip_base=True)
                raise e
        self.icomm.recv_timeout = self.recv_timeout
        self.ocomm.recv_timeout = self.recv_timeout
        if not dont_open:
            self.open()

    def _setup_comms(self, icomm_name, icomm_kwargs,
                     ocomm_name, ocomm_kwargs):
        r"""Set up input/output comms."""
        try:
            self.icomm = get_comm(icomm_name, **icomm_kwargs)
            self.ocomm = get_comm(ocomm_name, **ocomm_kwargs)
        except BaseException:
            self.close(skip_base=True)
            raise

    @classmethod
    def is_installed(cls):
        r"""bool: Is the comm installed."""
        return get_comm_class().is_installed()

    @property
    def maxMsgSize(self):
        r"""int: Maximum size of a single message that should be sent."""
        return min(self.icomm.maxMsgSize, self.ocomm.maxMsgSize)
        
    @classmethod
    def underlying_comm_class(self):
        r"""str: Name of underlying communication class."""
        return get_comm_class().underlying_comm_class()

    @classmethod
    def comm_count(cls):
        r"""int: Number of communication connections."""
        return get_comm_class().comm_count()

    @classmethod
    def new_comm_kwargs(cls, name, address=None,
                        icomm_name=None, ocomm_name=None,
                        icomm_comm=None, ocomm_comm=None,
                        icomm_kwargs=None, ocomm_kwargs=None, **kwargs):
        r"""Initialize communication with new comms.

        Args:
            name (str): Name for new comm.
            address (str, optional): Communication info. Default to None and
                address is taken from combination of input/output comm addresses
                that are provided or generated.
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

        """
        args = [name]
        if icomm_kwargs is None:
            icomm_kwargs = dict()
        if ocomm_kwargs is None:
            ocomm_kwargs = dict()
        if icomm_name is None:
            icomm_name = name
        if ocomm_name is None:
            ocomm_name = name
        icomm_name = icomm_kwargs.pop('name', icomm_name)
        ocomm_name = ocomm_kwargs.pop('name', ocomm_name)
        icomm_comm = icomm_kwargs.pop('comm', icomm_comm)
        ocomm_comm = ocomm_kwargs.pop('comm', ocomm_comm)
        icomm_class = get_comm_class(icomm_comm)
        ocomm_class = get_comm_class(ocomm_comm)
        icomm_kwargs['direction'] = 'recv'
        ocomm_kwargs['direction'] = 'send'
        ikwargs = copy.deepcopy(kwargs)
        okwargs = copy.deepcopy(kwargs)
        ikwargs.update(**icomm_kwargs)
        okwargs.update(**ocomm_kwargs)
        if address is None:
            if 'address' not in icomm_kwargs:
                iargs, ikwargs = icomm_class.new_comm_kwargs(icomm_name,
                                                             **icomm_kwargs)
            if 'address' not in ocomm_kwargs:
                oargs, okwargs = ocomm_class.new_comm_kwargs(ocomm_name,
                                                             **ocomm_kwargs)
        else:
            kwargs['address'] = address
            ikwargs['address'], okwargs['address'] = address.split(
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

    @property
    def opp_comms(self):
        r"""dict: Name/address pairs for opposite comms."""
        out = super(RPCComm, self).opp_comms
        out.update(**self.icomm.opp_comms)
        out.update(**self.ocomm.opp_comms)
        return out

    def open(self):
        r"""Open the connection."""
        super(RPCComm, self).open()
        try:
            self.icomm.open()
            self.ocomm.open()
        except BaseException as e:
            self.close()
            raise e

    def _close(self, linger=False):
        r"""Close the connection.

        Args:
            linger (bool, optional): If True, drain messages before closing the
                comm. Defaults to False.

        """
        ie = None
        oe = None
        try:
            if getattr(self, 'icomm', None) is not None:
                self.icomm.close()
        except BaseException as e:
            ie = e
        try:
            if getattr(self, 'ocomm', None) is not None:
                self.ocomm.close(linger=linger)
        except BaseException as e:
            oe = e
        if ie:
            raise ie
        if oe:
            raise oe
        super(RPCComm, self)._close(linger=linger)

    @property
    def is_open(self):
        r"""bool: True if the connection is open."""
        return self.icomm.is_open and self.ocomm.is_open

    # @property
    # def is_closed(self):
    #     r"""bool: True if the connection is closed."""
    #     return self.icomm.is_closed and self.ocomm.is_closed

    @property
    def n_msg_recv(self):
        r"""int: The number of messages in the input comm."""
        return self.icomm.n_msg_recv

    @property
    def n_msg_send(self):
        r"""int: The number of messages in the output comm."""
        return self.ocomm.n_msg_send

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
        timeout = kwargs.pop('timeout', self.recv_timeout)
        flag = self.send(*args, **kwargs)
        if not flag:
            self.debug("Send in call failed")
            return (False, backwards.unicode2bytes(''))
        self.debug("Sent")
        return self.recv(timeout=timeout)

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

    def drain_messages(self, direction=None, **kwargs):
        r"""Sleep while waiting for messages to be drained."""
        if direction is None:
            direction = self.direction
        if direction == 'send':
            self.ocomm.drain_messages(direction=direction, **kwargs)
        else:
            self.icomm.drain_messages(direction=direction, **kwargs)

    def purge(self):
        r"""Purge input and output comms."""
        self.icomm.purge()
        self.ocomm.purge()
        super(RPCComm, self).purge()
