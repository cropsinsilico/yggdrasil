from cis_interface.drivers.ServerDriver import ServerDriver


class RMQServerDriver(ServerDriver):
    r"""Class for handling an RMQ server.

    Args:
        *args: Arguments are passed to parent class.
        **kwargs: Keyword arguments are passed to parent class.

    """
    def __init__(self, *args, **kwargs):
        kwargs['comm'] = 'RMQComm'
        super(RMQServerDriver, self).__init__(*args, **kwargs)
