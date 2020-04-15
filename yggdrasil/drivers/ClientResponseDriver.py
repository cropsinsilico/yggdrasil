import uuid
from yggdrasil.drivers.ConnectionDriver import ConnectionDriver


class ClientResponseDriver(ConnectionDriver):
    r"""Class for handling client side RPC type communication.

    Args:
        model_response_address (str): The address of the channel used by the
            client model to receive responses.
        comm (str, optional): The comm class that should be used to
            communicate with the server response driver. Defaults to
            tools.get_default_comm().
        msg_id (str, optional): ID associate with the request message this
            driver was created to respond to. Defaults to new unique ID.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        comm (str): The comm class that should be used to communicate with the
            server response driver.
        msg_id (str): ID associate with the request message this driver was
            created to respond to.

    """

    _connection_type = None

    def __init__(self, model_response_address, request_name=None,
                 comm=None, msg_id=None, **kwargs):
        if msg_id is None:
            msg_id = str(uuid.uuid4())
        response_name = 'ClientResponse.%s' % msg_id
        if request_name is not None:
            response_name = request_name + '.' + response_name
        # Input communicator
        inputs = kwargs.get('inputs', [{}])
        inputs[0]['comm'] = comm
        inputs[0]['name'] = response_name
        inputs[0]['is_response_client'] = True
        kwargs['inputs'] = inputs
        # Output communicator
        outputs = kwargs.get('outputs', [{}])
        outputs[0]['comm'] = None
        outputs[0]['name'] = 'client_model_response.' + msg_id
        if model_response_address is not None:
            outputs[0]['address'] = model_response_address
        kwargs['outputs'] = outputs
        # Overall keywords
        kwargs['single_use'] = True
        super(ClientResponseDriver, self).__init__(response_name, **kwargs)
        self.comm = comm
        self.msg_id = msg_id

    @property
    def response_address(self):
        r"""str: Address of response comm."""
        return self.icomm.address
