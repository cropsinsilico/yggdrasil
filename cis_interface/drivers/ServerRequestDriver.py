from cis_interface.drivers.ConnectionDriver import ConnectionDriver
from cis_interface.drivers.ServerResponseDriver import ServerResponseDriver
from cis_interface.drivers.ClientRequestDriver import CIS_CLIENT_INI


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
        comm_address (str, optional): Address for the client request driver.
            Defaults to None and a new address is generated.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        comm (str): The comm class that should be used to communicate
            with the server driver. Defaults to _default_comm.
        comm_address (str): Address for the client request driver.
        response_drivers (list): Response drivers created for each request.
        nclients (int): Number of clients signed on.

    """

    def __init__(self, model_request_name, request_name=None,
                 comm=None, comm_address=None, **kwargs):
        if request_name is None:
            request_name = model_request_name + '_SERVER'
        # Input communicator
        icomm_kws = kwargs.get('icomm_kws', {})
        icomm_kws['comm'] = comm
        icomm_kws['name'] = request_name
        if comm_address is not None:
            icomm_kws['address'] = comm_address
        icomm_kws['close_on_eof_recv'] = False
        kwargs['icomm_kws'] = icomm_kws
        # Output communicator
        ocomm_kws = kwargs.get('ocomm_kws', {})
        ocomm_kws['comm'] = 'RPCComm'
        ocomm_kws['name'] = model_request_name
        ocomm_kws['reverse_names'] = True
        kwargs['ocomm_kws'] = ocomm_kws
        super(ServerRequestDriver, self).__init__(model_request_name, **kwargs)
        self.env[self.ocomm.icomm.name] = self.ocomm.icomm.address
        self.env[self.ocomm.ocomm.name] = self.ocomm.ocomm.address
        self.response_drivers = []
        self.nclients = 0
        assert(not hasattr(self, 'comm'))
        self.comm = comm
        self.comm_address = self.icomm.address
        # print 80*'='
        # print self.__class__
        # print self.env
        # print self.icomm.name, self.icomm.address
        # print self.ocomm.name, self.ocomm.address

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

    def on_eof(self):
        r"""On EOF, decrement number of clients. Only send EOF if the number
        of clients drops to 0."""
        self.nclients -= 1
        if self.nclients == 0:
            self.icomm._last_header['response_address'] = 'EOF'
            return super(ServerRequestDriver, self).on_eof()
        return ''

    def on_message(self, msg):
        r"""Process a message checking to see if it is a client signing on.

        Args:
            msg (bytes, str): Message to be processed.

        Returns:
            bytes, str: Processed message.

        """
        if msg == CIS_CLIENT_INI:
            self.nclients += 1
            msg = ''
        return super(ServerRequestDriver, self).on_message(msg)
    
    def send_message(self, *args, **kwargs):
        r"""Send a single message.

        Args:
            *args: Arguments are passed to parent class send_message.
            *kwargs: Keyword arguments are passed to parent class send_message.

        Returns:
            bool: Success or failure of send.

        """
        # Start response driver
        if self.response_address != 'EOF':
            with self.lock:
                if self.is_comm_open:
                    drv_args = [self.model_response_name,
                                self.model_response_address,
                                self.response_address]
                    drv_kwargs = dict(comm=self.comm)
                    response_driver = ServerResponseDriver(*drv_args, **drv_kwargs)
                    response_driver.start()
                    self.response_drivers.append(response_driver)
                else:
                    return False
        return super(ServerRequestDriver, self).send_message(*args, **kwargs)
