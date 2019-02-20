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
    _interpreter = sys.executable

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
