from yggdrasil.drivers.ConnectionDriver import ConnectionDriver


class InputDriver(ConnectionDriver):
    r"""Driver for receiving input from another model's comm via a local comm.

    Args:
        name (str): The name of the local message comm that the driver should
            connect to.
        args (str): The name of the other message comm that the driver should
            connect to.
        **kwargs: Additional keyword arguments are passed to parent class.

    """

    _connection_type = 'input'
    _direction = 'input'
    _schema_subtype_description = ('Connection between one or more comms/files '
                                   'and a model.')

    def __init__(self, name, args, **kwargs):
        kwargs.setdefault('inputs', [{}])
        kwargs['inputs'][0]['name'] = args
        if kwargs['inputs'][0].get('commtype', self._icomm_type) in ['rmq', 'RMQComm']:
            kwargs['inputs'][0]['queue'] = args
        super(InputDriver, self).__init__(name, **kwargs)
