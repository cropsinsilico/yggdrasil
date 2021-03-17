from yggdrasil.communication.CommBase import CommBase


class ValueComm(CommBase):

    _commtype = 'value'
    _schema_subtype_description = ('Constant value.')
    _schema_properties = {
        'count': {'type': 'integer', 'default': 1}}
    no_serialization = True

    def __init__(self, *args, **kwargs):
        self._is_open = False
        super(ValueComm, self).__init__(*args, **kwargs)
        assert(self.direction == 'recv')
        self.remaining = self.count

    @classmethod
    def is_installed(cls, language=None):
        r"""Determine if the necessary libraries are installed for this
        communication class.

        Args:
            language (str, optional): Specific language that should be checked
                for compatibility. Defaults to None and all languages supported
                on the current platform will be checked. If set to 'any', the
                result will be True if this comm is installed for any of the
                supported languages.

        Returns:
            bool: Is the comm installed.

        """
        if language == 'python':
            return True
        return False
        
    def open(self):
        r"""Open the connection."""
        super(ValueComm, self).open()
        self._is_open = True

    def _close(self, *args, **kwargs):
        r"""Close the connection."""
        self._is_open = False
        super(ValueComm, self)._close()

    @property
    def is_open(self):
        r"""bool: True if the connection is open."""
        return self._is_open
    
    @property
    def n_msg_recv(self):
        r"""int: The number of incoming messages in the connection."""
        return self.remaining

    def send(self, *args, **kwargs):
        r"""Send a message."""
        raise RuntimeError("Cannot send to a ValueComm.")

    def _recv(self, **kwargs):
        if self.remaining == 0:
            return True, self.eof_msg
        self.remaining -= 1
        return True, self.address

    @classmethod
    def get_testing_options(cls, **kwargs):
        r"""Method to return a dictionary of testing options for this class.

        Args:
            serializer (str, optional): The name of the serializer that should
                be used. If not provided, the _default_serializer class
                attribute will be used.

        Returns:
            dict: Dictionary of variables to use for testing. Key/value pairs:
                kwargs (dict): Keyword arguments for comms tested with the
                    provided content.
                send (list): List of objects to send to test file.
                recv (list): List of objects that will be received from a test
                    file that was sent the messages in 'send'.
                contents (bytes): Bytes contents of test file created by sending
                    the messages in 'send'.

        """
        msg = ['test', 1.0]
        count = 3
        objects = [msg for _ in range(count)]
        out = {'kwargs': {'address': msg, 'count': count},
               'send': objects,
               'msg': msg,
               'objects': objects,
               'recv': objects}
        return out

    def purge(self):
        r"""Purge all messages from the comm."""
        self.remaining = 0
