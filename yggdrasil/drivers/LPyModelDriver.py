import os
from yggdrasil.drivers.PythonModelDriver import PythonModelDriver
# try:  # pragma: lpy
#     from openalea import lpy
# except ImportError:  # pragma: no lpy
#     debug("Could not import openalea.lpy. "
#           + "LPy support will be disabled.")
#     lpy = None
# _lpy_installed = (lpy is not None)


_model_script = os.path.join(os.path.dirname(__file__), 'lpy_model.py')


class LPyModelDriver(PythonModelDriver):  # pragma: lpy
    r"""Class for running LPy models."""

    language = 'lpy'
    language_ext = '.lpy'
    # base_languages = ['python']  # Uncomment if PythonModelDriver not parent
    default_interpreter_flags = [_model_script]
    interface_dependencies = ['openalea.lpy']
    function_param = None
