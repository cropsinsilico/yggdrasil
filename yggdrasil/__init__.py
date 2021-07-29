r"""This package provides a framework for integrating models across languages
such that they can be run simultaneously, passing input back and forth."""
import os
import sys
import shutil
from ._version import get_versions
from yggdrasil import platform, config
from yggdrasil.runner import YggFunction
_test_package_name = None
_test_package = None
config.cfg_logging()


if platform._is_win:  # pragma: windows
    # This is required to fix crash on Windows in case of Ctrl+C
    # https://github.com/ContinuumIO/anaconda-issues/issues/905#issuecomment-232498034
    os.environ['FOR_DISABLE_CONSOLE_CTRL_HANDLER'] = 'T'


if not os.path.isfile(config.usr_config_file):  # pragma: config
    from yggdrasil.languages import install_languages
    shutil.copy(config.def_config_file, config.usr_config_file)
    install_languages.install_all_languages(from_setup=True)
    if not any([x.endswith(('yggconfig', 'yggconfig.exe', 'config'))
                for x in sys.argv]):
        # Don't configure if that is what is going to happen anyway
        config.update_language_config(verbose=True)


def import_as_function(model_yaml, service_address=None, **kwargs):
    r"""Import a model as a function from a yaml specification file.

    Args:
        model_yaml (str, list): Full path to one or more YAML specification
            files containing information defining a partial integration. If
            service_address is set, this should be the name of a service
            registered with the service manager running at the provided
            address.
        service_address (str, optional): Address for service manager that is
            capable of running the specified integration. Defaults to None
            and is ignored.
        **kwargs: Additional keyword arguments are passed to the
            YggFunction constructor.

    Returns:
        YggFunction: Callable wrapper for model.

    """
    return YggFunction(model_yaml, service_address=service_address, **kwargs)


__all__ = []
__version__ = get_versions()['version']
del get_versions
