from cis_interface.drivers.CommDriver import CommDriver


class OutputCommDriver(CommDriver):
    r"""Driver for output communication.

    Args:
        name (str): The name of the message queue that the driver should
            connect to.
        **kwargs: Additional keyword arguments are passed to the parent class.

    """
    def __init__(self, name, **kwargs):
        kwargs['direction'] = 'recv'
        super(OutputCommDriver, self).__init__(name, **kwargs)
