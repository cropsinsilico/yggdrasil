import uuid
from cis_interface.drivers.ConnectionDriver import ConnectionDriver


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

    def __init__(self, model_response_address, request_name=None,
                 comm=None, msg_id=None, **kwargs):
        if msg_id is None:
            msg_id = str(uuid.uuid4())
        response_name = 'ClientResponse.%s' % msg_id
        if request_name is not None:
            response_name = request_name + '.' + response_name
        # Input communicator
        icomm_kws = kwargs.get('icomm_kws', {})
        icomm_kws['comm'] = comm
        icomm_kws['name'] = response_name
        icomm_kws['is_response_client'] = True
        kwargs['icomm_kws'] = icomm_kws
        # Output communicator
        ocomm_kws = kwargs.get('ocomm_kws', {})
        ocomm_kws['comm'] = None
        ocomm_kws['name'] = 'client_model_response.' + msg_id
        if model_response_address is not None:
            ocomm_kws['address'] = model_response_address
        kwargs['ocomm_kws'] = ocomm_kws
        # Overall keywords
        kwargs['single_use'] = True
        super(ClientResponseDriver, self).__init__(response_name, **kwargs)
        self.comm = comm
        self.msg_id = msg_id

    @property
    def response_address(self):
        r"""str: Address of response comm."""
        return self.icomm.address
