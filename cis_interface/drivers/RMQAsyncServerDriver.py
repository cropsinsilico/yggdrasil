from cis_interface.drivers.ServerDriver import ServerDriver


class RMQAsyncServerDriver(ServerDriver):
    r"""Class for handling an RMQAsync server.

    Args:
        *args: Arguments are passed to parent class.
        **kwargs: Keyword arguments are passed to parent class.

    """
    def __init__(self, *args, **kwargs):
        kwargs['comm'] = 'RMQAsyncComm'
        super(RMQAsyncServerDriver, self).__init__(*args, **kwargs)
