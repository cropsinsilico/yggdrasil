r"""This package provides a framework for integrating models across languages
such that they can be run simultaneously, passing input back and forth."""
import os
import sys
import shutil
import logging
from ._version import get_versions
from yggdrasil import platform, config
logging.basicConfig()
logger = logging.getLogger(__name__)
    

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


__all__ = []
__version__ = get_versions()['version']
del get_versions
