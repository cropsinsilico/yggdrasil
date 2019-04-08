import os
from yggdrasil.drivers.PythonModelDriver import PythonModelDriver


_model_script = os.path.join(os.path.dirname(__file__), 'lpy_model.py')


class LPyModelDriver(PythonModelDriver):  # pragma: lpy
    r"""Class for running LPy models."""

    _schema_subtype_description = ('Model is an LPy system.')
    
    language = 'lpy'
    language_ext = '.lpy'
    # base_languages = ['python']  # Uncomment if PythonModelDriver not parent
    default_interpreter_flags = [_model_script]
    interface_dependencies = ['openalea.lpy']
    function_param = None
