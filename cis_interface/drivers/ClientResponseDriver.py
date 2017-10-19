import uuid
from cis_interface.drivers.ConnectionDriver import ConnectionDriver


class ClientResponseDriver(ConnectionDriver):
    r"""Class for handling client side RPC type communication.

    Args:
        model_response_name (str): The name of the channel used by the client
            model to receive responses.
        model_response_address (str): The address of the channel used by the
            client model to receive responses.
        comm (str, optional): The comm class that should be used to
            communicate with the server response driver. Defaults to
            _default_comm.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        comm (str): The comm class that should be used to communicate with the
            server response driver.

    """

    def __init__(self, model_response_name, model_response_address,
                 comm=None, **kwargs):
        response_name = 'ClientResponse.%s' % str(uuid.uuid4())
        # Input communicator
        icomm_kws = kwargs.get('icomm_kws', {})
        icomm_kws['comm'] = comm
        icomm_kws['name'] = response_name
        kwargs['icomm_kws'] = icomm_kws
        # Output communicator
        ocomm_kws = kwargs.get('ocomm_kws', {})
        ocomm_kws['comm'] = None
        ocomm_kws['name'] = model_response_name
        ocomm_kws['address'] = model_response_address
        kwargs['ocomm_kws'] = ocomm_kws
        super(ClientResponseDriver, self).__init__(response_name, **kwargs)
        assert(not hasattr(self, 'comm'))
        self.comm = comm
        # print 80*'='
        # print self.__class__
        # print self.env
        # print self.icomm.name, self.icomm.address
        # print self.ocomm.name, self.ocomm.address

    @property
    def model_response_name(self):
        r"""str: The name of the channel used by the client model to receive
        responses."""
        return self.ocomm.name

    @property
    def model_response_address(self):
        r"""str: The address of the channel used by the client model to receive
        responses."""
        return self.ocomm.address
    
    @property
    def response_name(self):
        r"""str: Name of response comm."""
        return self.icomm.name

    @property
    def response_address(self):
        r"""str: Address of response comm."""
        return self.icomm.address

    def send_message(self, *args, **kwargs):
        r"""Close the input comm once message sent.

        Args:
            *args: Arguments are passed to parent class send_message.
            *kwargs: Keyword arguments are passed to parent class send_message.

        Return:
            bool: Success or failure of send.

        """
        out = super(ClientResponseDriver, self).send_message(*args, **kwargs)
        self.icomm.close()
        return out
