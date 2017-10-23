from cis_interface.drivers.CommDriver import CommDriver


class RMQAsyncCommDriver(CommDriver):
    r"""Driver for communication via RMQAsync queues.

    Args:
        name (str): The name of the message queue that the driver should
            connect to.
        **kwargs: Additional keyword arguments are passed to the parent class.

    """
    def __init__(self, name, **kwargs):
        kwargs['comm'] = 'RMQAsyncComm'
        super(RMQAsyncCommDriver, self).__init__(name, **kwargs)
