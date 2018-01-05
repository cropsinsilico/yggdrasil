from cis_interface.drivers.ClientDriver import ClientDriver


class RMQAsyncClientDriver(ClientDriver):
    r"""Class for handling an RMQAsync client.

    Args:
        *args: Arguments are passed to parent class.
        **kwargs: Keyword arguments are passed to parent class.

    """
    def __init__(self, *args, **kwargs):
        kwargs['comm'] = 'RMQAsyncComm'
        super(RMQAsyncClientDriver, self).__init__(*args, **kwargs)
        self.timeout = 10.0
