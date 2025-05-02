from yggdrasil.communication import CommBase, NoMessages


class ModelFunctionComm(CommBase.CommBase):
    r"""Class for handling a direct call to a model function as a
    communicator."""
    
    _commtype = 'model_function'
    _dont_register = True
    no_serialization = 'normalize'
    pass_comm_message = True

    def __init__(self, name, **kwargs):
        self._model_function = None
        self._requests = []
        self._responses = []
        super(ModelFunctionComm, self).__init__(name, **kwargs)

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
        # TODO: Check registered python function wrappers
        # if language == 'python':
        #     return True
        return True

    def open(self):
        r"""Open the connection."""
        from yggdrasil.drivers.PythonModelDriver import PythonModelDriver
        super(ModelFunctionComm, self).open()
        language, model_file, function = self.address.split('::')
        self._model_function = PythonModelDriver.import_function(
            language, model_file, function)

    def _close(self, *args, **kwargs):
        r"""Close the connection."""
        self._model_function = None

    @property
    def _is_open(self):
        r"""bool: True if the connection is open."""
        return (self._model_function is not None)

    @property
    def n_msg_recv(self):
        r"""int: The number of incoming messages in the connection."""
        return len(self._responses)

    @property
    def n_msg_send(self):
        r"""int: The number of outgoing messages in the connection."""
        return len(self._requests)

    def _send(self, msg, **kwargs):
        if msg.flag == CommBase.FLAG_EOF:
            return True
        self._responses.append(self._model_function(*msg.tuple_args))
        return True

    def _recv(self, **kwargs):
        if len(self._responses) == 0:
            raise NoMessages("No responses")
        return (True, self._responses.pop(0))

    def purge(self):
        r"""Purge all messages from the comm."""
        self._requests.clear()
        self._responses.clear()
