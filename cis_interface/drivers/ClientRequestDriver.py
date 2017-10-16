from cis_interface.drivers.ConnectionDriver import ConnectionDriver
from cis_interface.drivers.ClientResponseDriver import ClientResponseDriver

# ----
# Client sends resquest to local client output comm
# Client recvs response from local client input comm
# ----
# Client request driver recvs from local client output comm
# Client request driver creates client response driver
# Client request driver sends to server request comm (w/ response comm header)
# ----
# Client response driver recvs from client response comm
# Client response driver sends to local client input comm
# ----
# Server recvs request from local server input comm
# Server sends response to local server output comm
# ----
# Server request driver recvs from server request comm
# Server request driver creates server response driver
# Server request driver sends to local server input comm
# ----
# Server response driver recvs from local server output comm
# Server response driver sends to client response comm
# ----


class ClientRequestDriver(ConnectionDriver):
    r"""Class for handling client side RPC type communication.

    Args:
        model_request_name (str): The name of the channel used by the client
            model to send requests.
        request_name (str, optional): The name of the channel used to
            send requests to the server request driver. Defaults to
            model_request_name + '_SERVER' if not set.
        comm (str, optional): The comm class that should be used to
            communicate with the server request driver. Defaults to
            _default_comm.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        comm (str): The comm class that should be used to communicate with the
            server request driver.
        response_drivers (list): Response drivers created for each request.

    """

    def __init__(self, model_request_name, request_name=None,
                 comm=None, **kwargs):
        if request_name is None:
            request_name = model_request_name + '_SERVER'
        # Input communicator
        icomm_kws = kwargs.get('icomm_kws', {})
        icomm_kws['comm'] = 'RPCComm'
        icomm_kws['name'] = model_request_name
        kwargs['icomm_kws'] = icomm_kws
        # Output communicator
        ocomm_kws = kwargs.get('ocomm_kws', {})
        ocomm_kws['comm'] = comm
        ocomm_kws['name'] = request_name
        kwargs['ocomm_kws'] = ocomm_kws
        super(ClientRequestDriver, self).__init__(model_request_name, **kwargs)
        self.response_drivers = []
        assert(not hasattr(self, 'comm'))
        self.comm = comm

    @property
    def model_request_name(self):
        r"""str: The name of the channel used by the client model to send
        requests."""
        return self.icomm.icomm.name

    @property
    def model_request_address(self):
        r"""str: The address of the channel used by the client model to send
        requests."""
        return self.icomm.icomm.address

    @property
    def model_response_name(self):
        r"""str: The name of the channel used by the client model to receive
        responses."""
        return self.icomm.ocomm.name

    @property
    def model_response_address(self):
        r"""str: The address of the channel used by the client model to receive
        responses."""
        return self.icomm.ocomm.address

    @property
    def request_name(self):
        r"""str: The name of the channel used to send requests to the server
        request driver."""
        return self.ocomm.name
    
    @property
    def request_address(self):
        r"""str: The address of the channel used to send requests to the server
        request driver."""
        return self.ocomm.address
    
    def terminate(self, *args, **kwargs):
        r"""Stop response drivers."""
        for x in self.response_drivers:
            x.terminate()
        super(ClientRequestDriver, self).terminate(*args, **kwargs)

    def send_message(self, *args, **kwargs):
        r"""Start a response driver for a request message and send message with
        header.

        Args:
            *args: Arguments are passed to parent class send_message.
            *kwargs: Keyword arguments are passed to parent class send_message.

        Returns:
            bool: Success or failure of send.

        """
        # Start response driver
        drv_args = [self.model_response_name, self.model_response_address]
        drv_kwargs = dict(comm=self.comm)
        with self.lock:
            response_driver = ClientResponseDriver(*drv_args, **drv_kwargs)
            response_driver.start()
            self.response_drivers.append(response_driver)
        # Send response address in header
        kwargs.setdefault('send_header', True)
        kwargs.setdefault('header_kwargs', {})
        kwargs['header_kwargs'].setdefault(
            'response_address', response_driver.response_address)
        return super(ClientRequestDriver, self).send_message(*args, **kwargs)
