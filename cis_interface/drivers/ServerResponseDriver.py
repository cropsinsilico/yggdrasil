import uuid
from cis_interface.drivers.ConnectionDriver import ConnectionDriver


class ServerResponseDriver(ConnectionDriver):
    r"""Class for handling server side RPC type communication.

    Args:
        request_name (str): The name of the request channel.
        request_address (str): The address of the request channel.
        server_comm (str, optional): The comm class that should be used to
            communicate with the server driver. Defaults to _default_comm.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        server_comm (str): The comm class that should be used to communicate
            with the server driver. Defaults to _default_comm.

    """

    def __init__(self, request_name, request_address,
                 server_comm=None, **kwargs):
        response_name = 'response.%s' % str(uuid.uuid4())
        self.server_comm = server_comm
        # Input communicator
        icomm_kws = kwargs.get('icomm_kws', {})
        icomm_kws['comm'] = None
        icomm_kws['name'] = request_name
        icomm_kws['address'] = request_address
        kwargs['icomm_kws'] = icomm_kws
        # Output communicator
        ocomm_kws = kwargs.get('ocomm_kws', {})
        ocomm_kws['comm'] = server_comm
        ocomm_kws['name'] = response_name
        kwargs['ocomm_kws'] = ocomm_kws
        super(ServerResponseDriver, self).__init__(response_name, **kwargs)

    @property
    def response_address(self):
        r"""str: Address of response comm."""
        return self.ocomm.address

    def on_message(self, msg):
        r"""Process a message and close the response comm.

        Args:
            msg (bytes, str): Message to be processed.

        Returns:
            bytes, str: Processed message.

        """
        self.ocomm.close()
        return msg
        
