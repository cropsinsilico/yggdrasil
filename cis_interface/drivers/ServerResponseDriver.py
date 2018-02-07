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

    def __init__(self, response_address, comm=None, msg_id=None, **kwargs):
        if msg_id is None:
            msg_id = str(uuid.uuid4())
        response_name = 'ServerResponse.%s' % msg_id
        # Input communicator from client model
        icomm_kws = kwargs.get('icomm_kws', {})
        icomm_kws['comm'] = None
        icomm_kws['name'] = 'server_model_response.' + msg_id
        kwargs['icomm_kws'] = icomm_kws
        # Output communicator to client response driver
        ocomm_kws = kwargs.get('ocomm_kws', {})
        ocomm_kws['comm'] = comm
        ocomm_kws['name'] = response_name
        if response_address is not None:
            ocomm_kws['address'] = response_address
        kwargs['ocomm_kws'] = ocomm_kws
        super(ServerResponseDriver, self).__init__(response_name, **kwargs)
        self.comm = comm
        self.msg_id = msg_id
        self._unused = True
        
    @property
    def is_valid(self):
        r"""bool: Returns True if the connection is unused and the parent class
        is valid."""
        with self.lock:
            return (super(ServerResponseDriver, self).is_valid and self._unused)

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

    def after_loop(self):
        r"""Send EOF to the client response driver."""
        super(ServerResponseDriver, self).after_loop(send_eof=False)
        
    def send_message(self, *args, **kwargs):
        r"""Set comm to used and then send the message.

        Args:
            *args: Arguments are passed to parent class send_message.
            *kwargs: Keyword arguments are passed to parent class send_message.

        Returns:
            bool: Success or failure of send.

        """
        with self.lock:
            self._unused = False
        out = super(ServerResponseDriver, self).send_message(*args, **kwargs)
        with self.lock:
            self.icomm.close()
        return out
