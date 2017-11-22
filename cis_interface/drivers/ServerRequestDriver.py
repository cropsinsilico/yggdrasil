from cis_interface.drivers.ConnectionDriver import ConnectionDriver
from cis_interface.drivers.ServerResponseDriver import ServerResponseDriver
from cis_interface.drivers.ClientRequestDriver import (
    CIS_CLIENT_INI, CIS_CLIENT_EOF)


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
        icomm_kws['no_suffix'] = True
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
        self.comm_address = self.icomm.address
        self._block_response = False

    @property
    def request_id(self):
        r"""str: Unique ID for the last message."""
        return self.icomm._last_header['id']

    @property
    def request_name(self):
        r"""str: The name of the channel used to receive requests from the
        client request driver."""
        return self.icomm.name
    
    @property
    def response_address(self):
        r"""str: The address of the channel used by the server response driver
        to send responses."""
        assert(isinstance(self.icomm._last_header, dict))
        return self.icomm._last_header['response_address']

    def terminate(self, *args, **kwargs):
        r"""Stop response drivers."""
        with self.lock:
            self._block_response = True
            for x in self.response_drivers:
                x.terminate()
            self.response_drivers = []
        super(ServerRequestDriver, self).terminate(*args, **kwargs)

    def on_model_exit(self):
        r"""Close RPC comm when model exits."""
        with self.lock:
            self.ocomm.close()
        super(ServerRequestDriver, self).on_model_exit()

    def after_loop(self):
        r"""After server model signs off."""
        with self.lock:
            self.icomm.close()
            if self.icomm._last_header is None:
                self.icomm._last_header = dict()
            if self.icomm._last_header.get('response_address', None) != CIS_CLIENT_EOF:
                self.icomm._last_header['response_address'] = CIS_CLIENT_EOF
                self.ocomm.send_eof()
        super(ServerRequestDriver, self).after_loop()
    
    def on_eof(self):
        r"""On EOF, decrement number of clients. Only send EOF if the number
        of clients drops to 0."""
        with self.lock:
            self.nclients -= 1
            if self.nclients == 0:
                self.icomm._last_header['response_address'] = CIS_CLIENT_EOF
                return super(ServerRequestDriver, self).on_eof()
        return ''

    def on_message(self, msg):
        r"""Process a message checking to see if it is a client signing on.

        Args:
            msg (bytes, str): Message to be processed.

        Returns:
            bytes, str: Processed message.

        """
        with self.lock:
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
        if self.ocomm.is_closed:
            return False
        # Start response driver
        if self.response_address != CIS_CLIENT_EOF:
            with self.lock:
                if (not self.is_comm_open) or self._block_response:
                    return False
                drv_args = [self.response_address]
                drv_kwargs = dict(comm=self.comm, msg_id=self.request_id)
                try:
                    response_driver = ServerResponseDriver(*drv_args, **drv_kwargs)
                    self.response_drivers.append(response_driver)
                    response_driver.start()
                except BaseException:
                    self.exception("Could not create/start response driver.")
                    return False
            # Send response address in header
            kwargs.setdefault('send_header', True)
            kwargs.setdefault('header_kwargs', {})
            kwargs['header_kwargs'].setdefault(
                'response_address', response_driver.model_response_address)
            kwargs['header_kwargs'].setdefault('id', self.request_id)
        return super(ServerRequestDriver, self).send_message(*args, **kwargs)
