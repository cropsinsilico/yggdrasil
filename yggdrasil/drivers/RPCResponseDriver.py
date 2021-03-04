from yggdrasil.drivers.ConnectionDriver import ConnectionDriver


class RPCResponseDriver(ConnectionDriver):
    r"""Class for handling client side RPC type communication.

    Args:
        model_response_address (str): The address of the channel used by the
            client model to receive responses.
        msg_id (str): ID associate with the request message this driver was
            created to respond to.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        msg_id (str): ID associate with the request message this driver was
            created to respond to.
        response_drivers (list): Response drivers created for each request.

    """

    _connection_type = 'rpc_response'

    def __init__(self, model_response_address, msg_id, **kwargs):
        # Input communicator
        inputs = kwargs.get('inputs', [{}])
        inputs[0]['name'] = 'server_model_response.' + msg_id
        inputs[0]['is_response_server'] = True
        kwargs['inputs'] = inputs
        # Output communicator
        outputs = kwargs.get('outputs', [{}])
        outputs[0]['name'] = 'client_model_response.' + msg_id
        outputs[0]['is_response_client'] = True
        if model_response_address is not None:
            outputs[0]['address'] = model_response_address
        kwargs['outputs'] = outputs
        # Overall keywords
        kwargs['single_use'] = True
        super(RPCResponseDriver, self).__init__('rpc_response.' + msg_id,
                                                **kwargs)
        self.msg_id = msg_id

    @property
    def response_address(self):
        r"""str: Address of response comm."""
        return self.icomm.address
