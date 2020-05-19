import uuid
from yggdrasil.drivers.ConnectionDriver import ConnectionDriver


class RPCResponseDriver(ConnectionDriver):
    r"""Class for handling client side RPC type communication.

    Args:
        model_response_address (str): The address of the channel used by the
            client model to receive responses.
        msg_id (str, optional): ID associate with the request message this
            driver was created to respond to. Defaults to new unique ID.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        msg_id (str): ID associate with the request message this driver was
            created to respond to.
        response_drivers (list): Response drivers created for each request.

    """

    _connection_type = 'rpc_response'

    def __init__(self, model_response_address, msg_id=None, **kwargs):
        if msg_id is None:
            msg_id = str(uuid.uuid4())
        # Input communicator
        icomm_kws = kwargs.get('icomm_kws', {})
        icomm_kws['name'] = 'server_model_response.' + msg_id
        # icomm_kws['is_response_client'] = True
        kwargs['icomm_kws'] = icomm_kws
        # Output communicator
        ocomm_kws = kwargs.get('ocomm_kws', {})
        ocomm_kws['name'] = 'client_model_response.' + msg_id
        ocomm_kws['address'] = model_response_address
        kwargs['ocomm_kws'] = ocomm_kws
        # Overall keywords
        kwargs['single_use'] = True
        super(RPCResponseDriver, self).__init__(icomm_kws['name'], **kwargs)
        self.msg_id = msg_id

    @property
    def response_address(self):
        r"""str: Address of response comm."""
        return self.icomm.address
