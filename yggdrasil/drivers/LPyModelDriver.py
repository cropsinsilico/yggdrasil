import os
from yggdrasil.languages import get_language_dir
from yggdrasil.drivers.PythonModelDriver import PythonModelDriver


_model_script = os.path.join(get_language_dir('lpy'), 'lpy_model.py')


class LPyModelDriver(PythonModelDriver):  # pragma: lpy
    r"""Class for running LPy models."""

    _schema_subtype_description = ('Model is an LPy system.')
    executable_type = 'dsl'
    language = 'lpy'
    language_ext = '.lpy'
    # base_languages = ['python']  # Uncomment if PythonModelDriver not parent
    default_interpreter_flags = [_model_script]
    interface_dependencies = ['openalea.lpy']
    function_param = None
    full_language = False
    is_dsl = True

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

    @classmethod
    def get_testing_options(cls, **kwargs):
        r"""Method to return a dictionary of testing options for this class.

        Args:
            **kwargs: Additional keyword arguments are passed to the parent
                class.

        Returns:
            dict: Dictionary of variables to use for testing. Key/value pairs:
                kwargs (dict): Keyword arguments for driver instance.
                deps (list): Dependencies to install.

        """
        out = super(LPyModelDriver, cls).get_testing_options(**kwargs)
        out['requires_partner'] = True
        return out
