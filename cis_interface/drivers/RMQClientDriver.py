from cis_interface.drivers.ClientDriver import ClientDriver


class RMQClientDriver(ClientDriver):
    r"""Class for handling an RMQ client.

    Args:
        *args: Arguments are passed to parent class.
        **kwargs: Keyword arguments are passed to parent class.

    """
    def __init__(self, *args, **kwargs):
        kwargs['comm'] = 'RMQComm'
        super(RMQClientDriver, self).__init__(*args, **kwargs)
