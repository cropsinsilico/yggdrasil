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
            communicate with the client request driver. Defaults to
            tools.get_default_comm().
        comm_address (str, optional): Address for the client request driver.
            Defaults to None and a new address is generated.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        comm (str): The comm class that should be used to communicate
            with the server driver. Defaults to tools.get_default_comm().
        comm_address (str): Address for the client request driver.
        response_drivers (list): Response drivers created for each request.
        nclients (int): Number of clients signed on.

    """

    _is_input = True

    def __init__(self, model_request_name, request_name=None,
                 comm=None, comm_address=None, **kwargs):
        if request_name is None:
            request_name = model_request_name + '_SERVER'
        # Input communicator
        icomm_kws = kwargs.get('icomm_kws', {})
        icomm_kws['comm'] = comm
        icomm_kws['name'] = request_name
        icomm_kws['no_suffix'] = True
        icomm_kws['is_server'] = True
        if comm_address is not None:
            icomm_kws['address'] = comm_address
        icomm_kws['close_on_eof_recv'] = False
        kwargs['icomm_kws'] = icomm_kws
        # Output communicator
        ocomm_kws = kwargs.get('ocomm_kws', {})
        ocomm_kws['comm'] = None
        ocomm_kws['name'] = model_request_name
        kwargs['ocomm_kws'] = ocomm_kws
        # Parent and attributes
        super(ServerRequestDriver, self).__init__(model_request_name, **kwargs)
        self.env[self.ocomm.name] = self.ocomm.address
        self.response_drivers = []
        self.nclients = 0
        self.comm = comm
        self.comm_address = self.icomm.address  # opp_address
        self._block_response = False

    @property
    def last_header(self):
        r"""dict: Information contained in the header of the last message
        received from the client model."""
        if self.icomm._last_header is None:
            raise AttributeError("No new requests have been received, so there " +
                                 "does not yet exist information required for " +
                                 "creating a response comm and fowarding the " +
                                 "request.")
        return self.icomm._last_header

    @property
    def request_id(self):
        r"""str: Unique ID for the last message."""
        return self.last_header['request_id']

    @property
    def request_name(self):
        r"""str: The name of the channel used to receive requests from the
        client request driver."""
        return self.icomm.name
    
    @property
    def response_address(self):
        r"""str: The address of the channel used by the server response driver
        to send responses."""
        return self.last_header['response_address']

    def close_response_drivers(self):
        r"""Close response drivers."""
        with self.lock:
            self.debug("Closing response drivers.")
            self._block_response = True
            for x in self.response_drivers:
                x.terminate()
            self.response_drivers = []

    def close_comm(self):
        r"""Close response drivers."""
        self.close_response_drivers()
        super(ServerRequestDriver, self).close_comm()

    def printStatus(self, *args, **kwargs):
        r"""Also print response drivers."""
        super(ServerRequestDriver, self).printStatus(*args, **kwargs)
        for x in self.response_drivers:
            x.printStatus(*args, **kwargs)

    def on_client_exit(self):
        r"""Close input comm to stop the loop."""
        self.debug('')
        self.wait_close_state('client exit')
        with self.lock:
            self.icomm.close()
        self.wait()
        self.confirm_output()
        self.debug('Finished')
    
    def on_eof(self):
        r"""On EOF, decrement number of clients. Only send EOF if the number
        of clients drops to 0."""
        with self.lock:
            self.nclients -= 1
            self.debug("Client signed off. nclients = %d", self.nclients)
            if self.nclients == 0:
                self.debug("All clients have signed off.")
                return super(ServerRequestDriver, self).on_eof()
        return self.icomm.serializer.empty_msg

    def on_message(self, msg):
        r"""Process a message checking to see if it is a client signing on.

        Args:
            msg (bytes, str): Message to be processed.

        Returns:
            bytes, str: Processed message.

        """
        with self.lock:
            if msg == CIS_CLIENT_INI:
                self.debug("New client signed on.")
                self.nclients += 1
                msg = self.icomm.serializer.empty_msg
                return msg
        return super(ServerRequestDriver, self).on_message(msg)
    
    def send_message(self, *args, **kwargs):
        r"""Send a single message.

        Args:
            *args: Arguments are passed to parent class send_message.
            **kwargs: Keyword arguments are passed to parent class send_message.

        Returns:
            bool: Success or failure of send.

        """
        if self.ocomm.is_closed:
            return False
        # Start response driver
        is_eof = kwargs.get('is_eof', False)
        if not is_eof:
            self.debug("Starting new ServerResponseDriver at: %s" %
                       self.response_address)
            with self.lock:
                if (not self.is_comm_open) or self._block_response:  # pragma: debug
                    self.debug("Comm closed, not creating response driver.")
                    return False
                drv_args = [self.response_address]
                drv_kwargs = dict(comm=self.comm, msg_id=self.request_id,
                                  request_name=self.name)
                try:
                    response_driver = ServerResponseDriver(*drv_args, **drv_kwargs)
                    self.response_drivers.append(response_driver)
                    response_driver.start()
                    self.debug("ServerResponseDriver started.")
                except BaseException:  # pragma: debug
                    self.exception("Could not create/start response driver.")
                    return False
            # Send response address in header
            kwargs.setdefault('header_kwargs', {})
            kwargs['header_kwargs'].setdefault(
                'response_address', response_driver.model_response_address)
            kwargs['header_kwargs'].setdefault('request_id', self.request_id)
        return super(ServerRequestDriver, self).send_message(*args, **kwargs)
