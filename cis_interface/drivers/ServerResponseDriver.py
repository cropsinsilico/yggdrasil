import uuid
from cis_interface.drivers.ConnectionDriver import ConnectionDriver


class ServerResponseDriver(ConnectionDriver):
    r"""Class for handling server side RPC type communication.

    Args:
        response_address (str): The address of the channel used to send
            responses to the client response driver.
        comm (str, optional): The comm class that should be used to
            communicate with the server resposne driver. Defaults to
            tools.get_default_comm().
        msg_id (str, optional): ID associate with the request message this
            driver was created to respond to. Defaults to new unique ID.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        comm (str): The comm class that should be used to communicate
            with the server driver. Defaults to tools.get_default_comm().
        msg_id (str): ID associate with the request message this driver was
            created to respond to.

    """

    def __init__(self, response_address, comm=None, msg_id=None,
                 request_name=None, **kwargs):
        if msg_id is None:
            msg_id = str(uuid.uuid4())
        response_name = 'ServerResponse.%s' % msg_id
        if request_name is not None:
            response_name = request_name + '.' + response_name
        # Input communicator from client model
        icomm_kws = kwargs.get('icomm_kws', {})
        icomm_kws['comm'] = None
        icomm_kws['name'] = 'server_model_response.' + msg_id
        icomm_kws['is_response_server'] = True
        kwargs['icomm_kws'] = icomm_kws
        # Output communicator to client response driver
        ocomm_kws = kwargs.get('ocomm_kws', {})
        ocomm_kws['comm'] = comm
        ocomm_kws['name'] = response_name
        if response_address is not None:
            ocomm_kws['address'] = response_address
        kwargs['ocomm_kws'] = ocomm_kws
        # Overall keywords
        kwargs['single_use'] = True
        super(ServerResponseDriver, self).__init__(response_name, **kwargs)
        self.comm = comm
        self.msg_id = msg_id
        
    @property
    def model_response_name(self):
        r"""str: The name of the channel used by the server model to send
        responses."""
        return self.icomm.name

    @property
    def model_response_address(self):
        r"""str: The address of the channel used by the server model to send
        responses."""
        return self.icomm.address
    
    @property
    def response_address(self):
        r"""str: The address of the channel used to send responses to the client
        response driver."""
        return self.ocomm.address
