from cis_interface.drivers.ConnectionDriver import ConnectionDriver


class ServerRequestDriver(ConnectionDriver):
    r"""Class for handling server side RPC type communication.

    Args:
        name (str): The name of the channel used by the server.
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
        icomm_kws['comm'] = 'ServerRequestComm'
        icomm_kws['name'] = args
        icomm_kws['base_comm'] = server_comm
        kwargs['icomm_kws'] = icomm_kws
        # Output communicator
        ocomm_kws = kwargs.get('ocomm_kws', {})
        ocomm_kws['comm'] = 'RPCComm'
        ocomm_kws['name'] = name
        kwargs['ocomm_kws'] = ocomm_kws
        super(ServerRequestDriver, self).__init__(name, **kwargs)
        self.response_drivers = []

    def on_message(self, msg):
        r"""Process a message and create the server reponse driver.

        Args:
            msg (bytes, str): Message to be processed.

        Returns:
            bytes, str: Processed message.

        """
        args = [self.ocomm.icomm.name, self.ocomm.icomm.address]
        kwargs = dict(server_comm=self.server_comm)
        response_driver = ServerResponseDriver(*args, **kwargs)
        self.response_drivers.append(response_driver)
        self.icomm.set_response_address(response_driver.response_address)
        return msg
        
