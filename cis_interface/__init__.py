r"""This package provides a framework for integrating models across languages
such that they can be run simultaneously, passing input back and forth."""
from cis_interface import platform
import os


if platform._is_win:  # pragma: windows
    # This is required to fix crash on Windows in case of Ctrl+C
    # https://github.com/ContinuumIO/anaconda-issues/issues/905#issuecomment-232498034
    os.environ['FOR_DISABLE_CONSOLE_CTRL_HANDLER'] = 'T'


# from cis_interface import backwards
# from cis_interface import platform
# from cis_interface import config
# from cis_interface import tools
# from cis_interface import interface
# from cis_interface import drivers
# from cis_interface import dataio
# from cis_interface import tests
# from cis_interface import examples
# from cis_interface import runner


# __all__ = ['backwards', 'platform', 'config', 'tools',
#            'interface', 'drivers', 'dataio',
#            'tests', 'examples', 'runner']

__all__ = []
