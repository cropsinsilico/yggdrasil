from yggdrasil.drivers.ServerDriver import ServerDriver


class RMQAsyncServerDriver(ServerDriver):
    r"""Class for handling an RMQAsync server.

    Args:
        *args: Arguments are passed to parent class.
        **kwargs: Keyword arguments are passed to parent class.

    """

    _connection_type = 'rmq_async_server'
    _schema_subtype_description = ('Connection between an asynchronous RabbitMQ '
                                   'server request comm and a model acting as a '
                                   'server.')
    
    def __init__(self, *args, **kwargs):
        kwargs['comm'] = 'RMQAsyncComm'
        super(RMQAsyncServerDriver, self).__init__(*args, **kwargs)
