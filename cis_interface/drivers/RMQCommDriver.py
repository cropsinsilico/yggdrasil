from cis_interface.drivers.CommDriver import CommDriver


class RMQCommDriver(CommDriver):
    r"""Driver for communication via RMQ queues.

    Args:
        name (str): The name of the message queue that the driver should
            connect to.
        **kwargs: Additional keyword arguments are passed to the parent class.

    Attributes:
        -

    """
    def __init__(self, name, **kwargs):
        kwargs['comm'] = 'RMQComm'
        super(RMQCommDriver, self).__init__(name, **kwargs)
