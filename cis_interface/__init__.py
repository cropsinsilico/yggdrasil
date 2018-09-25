r"""This package provides a framework for integrating models across languages
such that they can be run simultaneously, passing input back and forth."""
from cis_interface import platform
import os
import sys
import nose
from ._version import get_versions


if platform._is_win:  # pragma: windows
    # This is required to fix crash on Windows in case of Ctrl+C
    # https://github.com/ContinuumIO/anaconda-issues/issues/905#issuecomment-232498034
    os.environ['FOR_DISABLE_CONSOLE_CTRL_HANDLER'] = 'T'


def run_nose(verbose=False, nocapture=False, stop=False,
             nologcapture=False, withcoverage=False):  # pragma: debug
    r"""Run nose tests for the package.

    Args:
        verbose (bool, optional): If True, set nose option '-v' which
            increases the verbosity. Defaults to False.
        nocapture (bool, optional): If True, set nose option '--nocapture'
            which allows messages to be printed to stdout. Defaults to False.
        stop (bool, optional): If True, set nose option '--stop' which
            stops tests at the first failure. Defaults to False.
        nologcapture (bool, optional): If True, set nose option '--nologcapture'
            which allows logged messages to be printed. Defaults to False.
        withcoverage (bool, optional): If True, set nose option '--with-coverage'
            which invokes coverage. Defaults to False.

    """
    error_code = 0
    nose_argv = sys.argv
    if not nose_argv[-1].startswith('-'):
        test_dir = nose_argv.pop()
    else:
        test_dir = None
    nose_argv += ['--detailed-errors', '--exe']
    if verbose:
        nose_argv.append('-v')
    if nocapture:
        nose_argv.append('--nocapture')
    if stop:
        nose_argv.append('--stop')
    if nologcapture:
        nose_argv.append('--nologcapture')
    if withcoverage:
        nose_argv.append('--with-coverage')
        nose_argv.append('--cover-package=cis_interface')
    initial_dir = os.getcwd()
    package_dir = os.path.dirname(os.path.abspath(__file__))
    if (test_dir is None):
        test_dir = package_dir
    else:
        # Assumed relative to package directory
        if not os.path.isabs(test_dir):
            test_dir = os.path.join(package_dir, test_dir)
    os.chdir(test_dir)
    try:
        result = nose.run(argv=nose_argv)
        if not result:
            error_code = -1
    except BaseException:
        error_code = -1
    finally:
        os.chdir(initial_dir)
    return error_code


__all__ = []
__version__ = get_versions()['version']
del get_versions
