#
# This should not be used directly by modelers
#
import os
from logging import debug
from yggdrasil.drivers.ModelDriver import ModelDriver
from yggdrasil.drivers.PythonModelDriver import PythonModelDriver
try:  # pragma: lpy
    from openalea import lpy
except ImportError:  # pragma: no lpy
    debug("Could not import openalea.lpy. "
          + "LPy support will be disabled.")
    lpy = None
from yggdrasil.schema import register_component
_lpy_installed = (lpy is not None)


_model_script = os.path.join(os.path.dirname(__file__), 'lpy_model.py')


@register_component
class LPyModelDriver(ModelDriver):  # pragma: lpy
    r"""Class for running LPy models."""

    language = 'lpy'
    language_ext = '.lpy'
    base_languages = ['python']
    default_interpreter = PythonModelDriver.get_interpreter()
    default_interpreter_flags = [_model_script]

    @classmethod
    def is_language_installed(cls):
        r"""Determine if the interpreter/compiler for the associated programming
        language is installed.

        Returns:
            bool: True if the language interpreter/compiler is installed.

        """
        return _lpy_installed
