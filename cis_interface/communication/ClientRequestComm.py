from cis_interface.communication import get_comm_class


def ClientRequestComm(name, base_comm=None, **kwargs):
    r"""Wrapper to produce ClientRequestComm with arbitrary comm base.

    Args:
        name (str): The environment variable where communication address is
            stored.
        base_comm (str, optional): The name of the comm base class that should
            be used.
        **kwargs: Additional keyword arguments are passed to ClientRequestComm.

    Returns:
        ClientRequestComm: Communicator.

    """

    base = get_comm_class(base_comm)

    class ClientRequestComm(base):
        r"""Class for handling output to a request comm.

        Args:
            name (str): The environment variable where communication address is
                stored.
            **kwargs: Additional keywords arguments are passed to parent class.

        Attributes:
            response_address (str): Address of response queue that should be
                sent in the header of all messages.

        """
        def __init__(self, *args, **kwargs):
            super(ClientRequestComm, self).__init__(*args, **kwargs)
            self.response_address = None

        def get_header(self, msg):
            r"""Create a dictionary of message properties.

            Args:
                msg (str): Message to get header for.

            Returns:
               dict: Properties that should be encoded in a messaged header.

            Raises:
                AssertionError: If the response_address is None.

            """
            assert(self.response_address is not None)
            out = super(ClientRequestComm, self).get_header(msg)
            out['response_address'] = self.response_address
            return out

        def set_response_address(self, address):
            r"""Sent the reponse address.

            Args:
                address (str): Address for response comm.

            """
            self.response_address = address

        def send_multipart(self, *args, **kwargs):
            r"""Force send of a multipart message with a header.

            Args:
                *args: Arguments are passed to parent send_multipart.
                **kwargs: Keyword arguments are passed to parent send_multipart.

            Returns:
                bool: Success or failure of send.

            """
            kwargs['send_header'] = True
            return super(ClientRequestComm, self).send_multipart(*args, **kwargs)

    return ClientRequestComm(name, **kwargs)
