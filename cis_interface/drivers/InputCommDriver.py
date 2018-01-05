from cis_interface.drivers.CommDriver import CommDriver


class InputCommDriver(CommDriver):
    r"""Driver for input communication.

    Args:
        name (str): The name of the message queue that the driver should
            connect to.
        **kwargs: Additional keyword arguments are passed to the parent class.

    """
    def __init__(self, name, **kwargs):
        kwargs['direction'] = 'send'
        super(InputCommDriver, self).__init__(name, **kwargs)
