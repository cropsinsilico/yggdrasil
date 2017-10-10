import os
from cis_interface.communication import DefaultComm, CommBase


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
        **kwargs: Additional keywords arguments are passed to parent class.

    Attributes:
        icomm (DefaultComm): Input comm.
        ocomm (DefaultComm): Output comm.

    """
    def __init__(self, name, icomm_kwargs=None, ocomm_kwargs=None,
                 dont_open=False, **kwargs):
        if icomm_kwargs is None:
            icomm_kwargs = dict()
        if ocomm_kwargs is None:
            ocomm_kwargs = dict()
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
            self.icomm = DefaultComm(icomm_name, **icomm_kwargs)
            self.ocomm = DefaultComm(ocomm_name, **ocomm_kwargs)
        else:
            self.icomm = DefaultComm(icomm_name, **icomm_kwargs)
            self.ocomm = DefaultComm(ocomm_name, **ocomm_kwargs)
            kwargs.setdefault('address', _rpc_address_split.join(
                [self.icomm.address, self.ocomm.address]))
            super(RPCComm, self).__init__(name, dont_open=True, **kwargs)
        if not dont_open:
            self.open()

    @property
    def comm_count(self):
        r"""int: Number of communication connections."""
        return self.icomm.comm_count

    @classmethod
    def new_comm_kwargs(cls, *args, **kwargs):
        r"""Initialize communication with new queue."""
        iargs, ikwargs = DefaultComm.new_comm_kwargs(*args, **kwargs)
        oargs, okwargs = DefaultComm.new_comm_kwargs(*args, **kwargs)
        kwargs.setdefault('address', _rpc_address_split.join([
            ikwargs['address'], okwargs['address']]))
        return args, kwargs

    def opp_comm_kwargs(self):
        r"""Get keyword arguments to initialize communication with opposite
        comm object.

        Returns:
            dict: Keyword arguments for opposite comm object.

        """
        kwargs = {'comm': self.comm_class}
        adds = self.address.split(_rpc_address_split)
        kwargs['address'] = _rpc_address_split.join([adds[1], adds[0]])
        kwargs['serialize'] = self.meth_serialize
        kwargs['deserialize'] = self.meth_deserialize
        return kwargs

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
    def send(self, msg, *args, **kwargs):
        r"""Send a message shorter than PSI_MSG_MAX to input comm."""
        return self.ocomm.send(msg, *args, **kwargs)

    def send_nolimit(self, msg, *args, **kwargs):
        r"""Send a message larger than PSI_MSG_MAX to output comm."""
        return self.ocomm.send_nolimit(msg, *args, **kwargs)

    # RECV METHODS
    def recv(self, *args, **kwargs):
        r"""Receive a message shorter than PSI_MSG_MAX from input comm."""
        return self.icomm.recv(*args, **kwargs)

    def recv_nolimit(self, *args, **kwargs):
        r"""Receive a message larger than PSI_MSG_MAX from input comm."""
        return self.icomm.recv_nolimit(*args, **kwargs)

    # CALL
    def call(self, msg):
        r"""Do RPC call for request message shorter than PSI_MSG_MAX."""
        flag = self.send(msg)
        if not flag:
            return (False, '')
        return self.recv(timeout=False)

    def call_nolimit(self, msg):
        r"""Do RPC call for request message larger than PSI_MSG_MAX."""
        flag = self.send_nolimit(msg)
        if not flag:
            return (False, '')
        return self.recv_nolimit(timeout=False)
