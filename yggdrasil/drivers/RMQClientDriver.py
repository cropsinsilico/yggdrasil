from yggdrasil.drivers.ClientDriver import ClientDriver


class RMQClientDriver(ClientDriver):
    r"""Class for handling an RMQ client.

    Args:
        *args: Arguments are passed to parent class.
        **kwargs: Keyword arguments are passed to parent class.

    """

    _connection_type = 'rmq_client'
    _schema_subtype_description = ('Connection between a model acting as a '
                                   'client and a RabbitMQ server request comm.')
    
    def __init__(self, *args, **kwargs):
        kwargs['comm'] = 'RMQComm'
        super(RMQClientDriver, self).__init__(*args, **kwargs)
