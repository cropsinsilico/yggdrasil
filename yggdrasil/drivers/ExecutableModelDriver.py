from yggdrasil.drivers.ModelDriver import ModelDriver
from yggdrasil.schema import register_component


@register_component
class ExecutableModelDriver(ModelDriver):
    r"""Class for running executable based models."""

    _language = 'executable'

    @classmethod
    def language_executable(cls):
        r"""Command/arguments required to compile/run a model written in this
        language from the command line.

        Returns:
            list: Name of (or path to) compiler/interpreter executable and any
                flags required to run the compiler/interpreter from the command
                line.

        """
        return None

    @classmethod
    def is_language_installed(cls):
        r"""Determine if the interpreter/compiler for the associated programming
        language is installed.

        Returns:
            bool: True if the language interpreter/compiler is installed.

        """
        return True

    @classmethod
    def is_language_configured(cls):
        r"""Determine if the appropriate configuration has been performed (e.g.
        installation of supporting libraries etc.)

        Returns:
            bool: True if the language has been configured.

        """
        return True

    @classmethod
    def is_comm_installed(self):
        r"""Determine if a comm is installed for the associated programming
        language.

        Returns:
            bool: True if a comm is installed for this language.

        """
        return True  # executables presumable include comms
