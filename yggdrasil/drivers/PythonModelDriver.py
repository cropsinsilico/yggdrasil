#
# This should not be used directly by modelers
#
import os
import sys
from yggdrasil.drivers.InterpretedModelDriver import InterpretedModelDriver
from yggdrasil.schema import register_component


_top_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '../'))
_incl_interface = os.path.join(_top_dir, 'interface')
_incl_io = os.path.join(_top_dir, 'io')


@register_component
class PythonModelDriver(InterpretedModelDriver):
    r"""Class for running Python models."""

    _language = 'python'
    _language_ext = '.py'

    @classmethod
    def language_interpreter(cls):
        r"""Command/arguments required to run a model written in this language
        from the command line.

        Returns:
            list: Name of (or path to) interpreter executable and any flags
                required to run the interpreter from the command line.

        """
        return [sys.executable]
        
    @classmethod
    def is_language_installed(self):
        r"""Determine if this model driver is installed on the current
        machine.

        Returns:
            bool: Truth of if this model driver can be run on the current
                machine.

        """
        # This is being run so python exists
        return True
