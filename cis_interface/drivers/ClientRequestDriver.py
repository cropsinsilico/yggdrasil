from cis_interface.drivers.ConnectionDriver import ConnectionDriver

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
        name (str): The name of the channel used by the client.
        args (str, optional): The name of the server driver channel. Defaults to
            name + '_SERVER' if not set.
        server_comm (str, optional): The comm class that should be used to
            communicate with the server driver. Defaults to _default_comm.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        server_comm (str): The comm class that should be used to communicate
            with the server driver. Defaults to _default_comm.
        response_drivers (list): Response drivers created for each request.

    """

    def __init__(self, name, args=None, server_comm=None, **kwargs):
        if args is None:
            args = name + '_SERVER'
        self.server_comm = server_comm
        # Input communicator
        icomm_kws = kwargs.get('icomm_kws', {})
        icomm_kws['comm'] = 'RPCComm'
        icomm_kws['name'] = name
        kwargs['icomm_kws'] = icomm_kws
        # Output communicator
        ocomm_kws = kwargs.get('ocomm_kws', {})
        ocomm_kws['comm'] = 'ClientRequestComm'
        ocomm_kws['base_comm'] = server_comm
        ocomm_kws['name'] = args
        kwargs['ocomm_kws'] = ocomm_kws
        super(ClientRequestDriver, self).__init__(name, **kwargs)
        self.response_drivers = []

    def on_message(self, msg):
        r"""Process a message and create the client reponse driver.

        Args:
            msg (bytes, str): Message to be processed.

        Returns:
            bytes, str: Processed message.

        """
        args = [self.icomm.ocomm.name, self.icomm.ocomm.address]
        kwargs = dict(server_comm=self.server_comm)
        response_driver = ClientResponseDriver(*args, **kwargs)
        self.response_drivers.append(response_driver)
        self.ocomm.set_response_address(response_driver.response_address)
        return msg
        
