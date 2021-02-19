from yggdrasil.drivers.ConnectionDriver import ConnectionDriver


class OutputDriver(ConnectionDriver):
    r"""Driver for sending output to another model's comm via a local comm.

    Args:
        name (str): The name of the local message comm that the driver should
            connect to.
        args (str): The name of the other message comme that the driver should
            connect to.
        **kwargs: Additional keyword arguments are passed to parent class.

    """

    _connection_type = 'output'
    _direction = 'output'
    _schema_subtype_description = ('Connection between a model '
                                   'and one or more comms/files.')

    def __init__(self, name, args, **kwargs):
        kwargs.setdefault('outputs', [{}])
        kwargs['outputs'][0]['name'] = args
        if kwargs['outputs'][0].get('commtype', self._ocomm_type) in ['rmq', 'RMQComm']:
            kwargs['outputs'][0]['queue'] = args
        super(OutputDriver, self).__init__(name, **kwargs)
