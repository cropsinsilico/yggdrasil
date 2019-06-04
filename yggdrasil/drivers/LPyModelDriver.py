import os
from yggdrasil.languages import get_language_dir
from yggdrasil.drivers.PythonModelDriver import PythonModelDriver


_model_script = os.path.join(get_language_dir('lpy'), 'lpy_model.py')


class LPyModelDriver(PythonModelDriver):  # pragma: lpy
    r"""Class for running LPy models."""

    _schema_subtype_description = ('Model is an LPy system.')
    
    language = 'lpy'
    language_ext = '.lpy'
    # base_languages = ['python']  # Uncomment if PythonModelDriver not parent
    default_interpreter_flags = [_model_script]
    interface_dependencies = ['openalea.lpy']
    function_param = None

    @classmethod
    def language_version(cls, **kwargs):
        r"""Determine the version of this language.

        Args:
            **kwargs: Keyword arguments are passed to cls.run_executable.

        Returns:
            str: Version of compiler/interpreter for this language.

        """
        try:
            import openalea.lpy
            return openalea.lpy.__version__.LPY_VERSION_STR
        except ImportError:  # pragma: debug
            raise RuntimeError("openalea.lpy not installed.")
