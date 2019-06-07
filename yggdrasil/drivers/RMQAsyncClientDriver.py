from yggdrasil.drivers.ClientDriver import ClientDriver


class RMQAsyncClientDriver(ClientDriver):
    r"""Class for handling an RMQAsync client.

    Args:
        *args: Arguments are passed to parent class.
        **kwargs: Keyword arguments are passed to parent class.

    """

    _connection_type = 'rmq_async_client'
    _schema_subtype_description = ('Connection between a model acting as a '
                                   'client and an asynchronous RabbitMQ server '
                                   'request comm.')
    
    def __init__(self, *args, **kwargs):
        kwargs['comm'] = 'RMQAsyncComm'
        super(RMQAsyncClientDriver, self).__init__(*args, **kwargs)
        self.timeout = 10.0
