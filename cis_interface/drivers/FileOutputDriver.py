import os
from cis_interface.interface.PsiInterface import PSI_MSG_EOF
from cis_interface.drivers.ConnectionDriver import ConnectionDriver


class FileOutputDriver(ConnectionDriver):
    r"""Class to handle output of received messages to a file.

    Args:
        name (str): Name of the output queue to receive messages from.
        args (str): Path to the file that messages should be written to.
        **kwargs: Additional keyword arguments are passed to the parent class.

    """
    def __init__(self, name, args, **kwargs):
        # icomm_kws = kwargs.get('icomm_kws', {})
        ocomm_kws = kwargs.get('ocomm_kws', {})
        ocomm_kws['comm'] = 'FileComm'
        ocomm_kws['address'] = args
        kwargs['ocomm_kws'] = ocomm_kws
        super(FileOutputDriver, self).__init__(name, **kwargs)
        self.debug('(%s)', args)

    @property
    def eof_msg(self):
        r"""str: Message indicating end of file."""
        return PSI_MSG_EOF

    def recv_message(self):
        r"""Receive a message from the queue and check if it is end of file.

        Returns:
            str: Message.

        """
        data = super(FileOutputDriver, self).recv_message()
        if isinstance(data, str) and (data == self.eof_msg):
            self.on_eof()
            data = ''
        return data

    def on_eof(self):
        r"""Actions to perform when the end of file is reached."""
        self.ocomm.close()
