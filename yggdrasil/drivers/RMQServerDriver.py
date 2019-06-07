from yggdrasil.drivers.ServerDriver import ServerDriver


class RMQServerDriver(ServerDriver):
    r"""Class for handling an RMQ server.

    Args:
        *args: Arguments are passed to parent class.
        **kwargs: Keyword arguments are passed to parent class.

    """

    _connection_type = 'rmq_server'
    _schema_subtype_description = ('Connection between a RabbitMQ server request '
                                   'comm and a model acting as a server.')
    
    def __init__(self, *args, **kwargs):
        kwargs['comm'] = 'RMQComm'
        super(RMQServerDriver, self).__init__(*args, **kwargs)
