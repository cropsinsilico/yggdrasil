from cis_interface.drivers.ConnectionDriver import ConnectionDriver
from cis_interface.drivers.ServerResponseDriver import ServerResponseDriver


class ServerRequestDriver(ConnectionDriver):
    r"""Class for handling server side RPC type communication.

    Args:
        model_request_name (str): The name of the channel used by the server
            model to send requests.
        request_name (str, optional): The name of the channel that should be
            used to receive requests from the client request driver. Defaults to
            model_request_name + '_SERVER' if not set.
        comm (str, optional): The comm class that should be used to
            communicate with the client request driver. Defaults to _default_comm.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        comm (str): The comm class that should be used to communicate
            with the server driver. Defaults to _default_comm.
        response_drivers (list): Response drivers created for each request.

    """

    def __init__(self, model_request_name, request_name=None,
                 comm=None, **kwargs):
        if request_name is None:
            request_name = model_request_name + '_SERVER'
        # Input communicator
        icomm_kws = kwargs.get('icomm_kws', {})
        icomm_kws['comm'] = comm
        icomm_kws['name'] = request_name
        kwargs['icomm_kws'] = icomm_kws
        # Output communicator
        ocomm_kws = kwargs.get('ocomm_kws', {})
        ocomm_kws['comm'] = 'RPCComm'
        ocomm_kws['name'] = model_request_name
        kwargs['ocomm_kws'] = ocomm_kws
        super(ServerRequestDriver, self).__init__(model_request_name, **kwargs)
        self.response_drivers = []
        assert(not hasattr(self, 'comm'))
        self.comm = comm

    @property
    def model_request_name(self):
        r"""str: The name of the channel used by the server model to receive
        requests."""
        return self.ocomm.ocomm.name

    @property
    def model_request_address(self):
        r"""str: The address of the channel used by the server model to receive
        requests."""
        return self.ocomm.ocomm.address

    @property
    def model_response_name(self):
        r"""str: The name of the channel used by the server model to send
        responses."""
        return self.ocomm.icomm.name

    @property
    def model_response_address(self):
        r"""str: The address of the channel used by the server model to send
        responses."""
        return self.ocomm.icomm.address
    
    @property
    def request_name(self):
        r"""str: The name of the channel used to receive requests from the
        client request driver."""
        return self.icomm.name
    
    @property
    def request_address(self):
        r"""str: The address of the channel used to receive requests from the
        client request driver."""
        return self.icomm.address
    
    @property
    def response_address(self):
        r"""str: The address of the channel used by the server response driver
        to send responses."""
        assert(isinstance(self.icomm._last_header, dict))
        return self.icomm._last_header['response_address']

    def terminate(self, *args, **kwargs):
        r"""Stop response drivers."""
        for x in self.response_drivers:
            x.terminate()
        super(ServerRequestDriver, self).terminate(*args, **kwargs)

    def send_message(self, *args, **kwargs):
        r"""Send a single message.

        Args:
            *args: Arguments are passed to parent class send_message.
            *kwargs: Keyword arguments are passed to parent class send_message.

        Returns:
            bool: Success or failure of send.

        """
        # Start response driver
        drv_args = [self.model_response_name, self.model_response_address,
                    self.response_address]
        drv_kwargs = dict(comm=self.comm)
        response_driver = ServerResponseDriver(*drv_args, **drv_kwargs)
        response_driver.start()
        self.response_drivers.append(response_driver)
        return super(ServerRequestDriver, self).send_message(*args, **kwargs)
