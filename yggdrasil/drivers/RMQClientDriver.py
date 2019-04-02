from yggdrasil.drivers.ClientDriver import ClientDriver


class RMQClientDriver(ClientDriver):
    r"""Class for handling an RMQ client.

    Args:
        *args: Arguments are passed to parent class.
        **kwargs: Keyword arguments are passed to parent class.

    """

    _connection_type = 'rmq_client'
    
    def __init__(self, *args, **kwargs):
        kwargs['comm'] = 'RMQComm'
        super(RMQClientDriver, self).__init__(*args, **kwargs)
