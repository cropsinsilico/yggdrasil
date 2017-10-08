import os
from cis_interface.drivers.ConnectionDriver import ConnectionDriver


class FileInputDriver(ConnectionDriver):
    r"""Class that sends messages read from a file.

    Args:
        name (str): Name of the queue that messages should be sent to.
        args (str): Path to the file that messages should be read from.
        **kwargs: Additional keyword arguments are passed to the parent class.

    """
    def __init__(self, name, args, **kwargs):
        icomm_kws = kwargs.get('icomm_kws', {})
        # ocomm_kws = kwargs.get('ocomm_kws', {})
        icomm_kws['comm'] = 'FileComm'
        icomm_kws['address'] = args
        kwargs['icomm_kws'] = icomm_kws
        super(FileInputDriver, self).__init__(name, **kwargs)
        self.debug('(%s)', args)

    def recv_message(self):
        r"""Read a message from the file.

        Returns:
            str: Message.

        """
        data = super(FileInputDriver, self).recv_message()
        if isinstance(data, str) and len(data) == 0:
            self.on_eof()
        return data

    def on_eof(self):
        r"""Actions to perform when the end of file is reached."""
        self.icomm.close()
