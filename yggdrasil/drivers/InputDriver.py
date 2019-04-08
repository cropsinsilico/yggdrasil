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
        kwargs.setdefault('icomm_kws', {})
        kwargs['icomm_kws']['name'] = args
        if kwargs['icomm_kws'].get('comm', self._icomm_type) == 'RMQComm':
            kwargs['icomm_kws']['queue'] = args
        super(InputDriver, self).__init__(name, **kwargs)
