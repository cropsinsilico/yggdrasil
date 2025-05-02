from yggdrasil.communication.CommBase import CommBase


class DummyComm(CommBase):
    r"""Dummy communicator that dosn't actually do anything."""

    _commtype = 'dummy'
    _schema_subtype_description = ('Dummy communicator.')
    _dont_register = True
    no_serialization = True

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
        return True
        
    def open(self):
        r"""Open the connection."""
        super(DummyComm, self).open()
        self._openned = True

    def _close(self, *args, **kwargs):
        r"""Close the connection."""
        self._openned = False
        super(DummyComm, self)._close()

    def send(self, *args, **kwargs):
        r"""Send a message."""
        raise RuntimeError("Cannot send to a DummyComm.")

    def recv(self, **kwargs):
        r"""Receive a message."""
        raise RuntimeError("Cannot receive from a DummyComm.")
