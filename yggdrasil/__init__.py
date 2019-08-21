r"""This package provides a framework for integrating models across languages
such that they can be run simultaneously, passing input back and forth."""
from yggdrasil import platform
import os
import sys
import glob
import logging
import subprocess
import importlib
from ._version import get_versions
_test_package_name = None
_test_package = None
logger = logging.getLogger(__name__)
order = ['pytest', 'nose']
try:
    _test_package_name = order[0]
    _test_package = importlib.import_module(_test_package_name)
except ImportError:  # pragma: debug
    try:
        _test_package_name = order[1]
        _test_package = importlib.import_module(_test_package_name)
    except ImportError:
        _test_package_name = None
        _test_package = None
    

if platform._is_win:  # pragma: windows
    # This is required to fix crash on Windows in case of Ctrl+C
    # https://github.com/ContinuumIO/anaconda-issues/issues/905#issuecomment-232498034
    os.environ['FOR_DISABLE_CONSOLE_CTRL_HANDLER'] = 'T'


def expand_and_add(path, path_list, dir_list):  # pragma: no cover
    r"""Expand the specified path and add it's expanded forms to the provided
    list.

    Args:
        path (str): Absolute/relative path with or without regex wildcard
            expressions to expand.
        path_list (list): Existing list that expansions should be added to.
        dir_list (list): Directories that should be tried for relative paths.

    Returns:
        int: The number of expansions added to path_list.

    """
    if os.path.isabs(path):
        matches = sorted(glob.glob(path))
        path_list += matches
        return len(matches)
    # Try checking for function
    for func_sep in ['::', ':']:
        if (func_sep in path):
            prepath, mod = path.rsplit(func_sep, 1)
            nadded = expand_and_add(prepath, path_list, dir_list)
            if nadded:
                for i in range(-nadded, 0):
                    path_list[i] += '%s%s' % (func_sep, mod)
                return nadded
    # Try directory prefixes
    for path_prefix in dir_list:
        nadded = expand_and_add(os.path.join(path_prefix, path),
                                path_list, dir_list)
        if nadded:
            return nadded
    return 0


def run_tsts(verbose=True, nocapture=True, stop=True,
             nologcapture=True, withcoverage=True,
             withexamples=False):  # pragma: no cover
    r"""Run tests for the package. Relative paths are interpreted to be
    relative to the package root directory.

    Args:
        verbose (bool, optional): If True, set option '-v' which
            increases the verbosity. Defaults to True.
        nocapture (bool, optional): If True, set option '--nocapture'
            ('--capture=no' with pytest) which allows messages to be printed to
            stdout. Defaults to True.
        stop (bool, optional): If True, set option '--stop' ('--exitfirst' for
            pytest) which stops tests at the first failure. Defaults to True.
        nologcapture (bool, optional): If True, set option '--nologcapture'
            which allows logged messages to be printed. Defaults to True.
        withcoverage (bool, optional): If True, set option '--with-coverage'
            which invokes coverage. Defaults to True.
        withexamples (bool, optional): If True, example testing will be
            enabled. Defaults to False.

    """
    if _test_package is None:
        raise RuntimeError("Could not locate test runner pytest or nose.")
    elif _test_package_name == 'pytest':
        test_cmd = 'pytest'
    elif _test_package_name == 'nose':
        test_cmd = 'nosetests'
    else:
        raise RuntimeError("Unsupported test package: '%s'" % _test_package_name)
    initial_dir = os.getcwd()
    package_dir = os.path.dirname(os.path.abspath(__file__))
    error_code = 0
    argv = [test_cmd]
    test_paths = []
    opt_val = 0
    for x in sys.argv:
        if opt_val > 0:
            argv.append(x)
            opt_val -= 1
        elif x.endswith('yggtest'):
            pass
        elif x == '--nocover':
            withcoverage = False
        elif x in ['--withexamples', '--with-examples']:
            withexamples = True
        elif x.startswith('-'):
            argv.append(x)
            if (_test_package_name == 'pytest') and (x in ['-c']):
                opt_val = 1
        else:
            test_paths.append(x)
    if _test_package_name == 'nose':
        argv += ['--detailed-errors', '--exe']
    if verbose:
        argv.append('-v')
    if nocapture:
        argv.append('-s')
    if stop:
        argv.append('-x')
    if nologcapture and (_test_package_name == 'nose'):
        argv.append('--nologcapture')
    if withcoverage:
        if _test_package_name == 'nose':
            argv.append('--with-coverage')
            argv.append('--cover-package=yggdrasil')
        elif _test_package_name == 'pytest':
            argv.append('--cov=%s' % package_dir)
    # Get expanded tests to allow for paths that are relative to either the
    # yggdrasil root directory or the current working directory
    expanded_test_paths = []
    if not test_paths:
        expanded_test_paths.append(package_dir)
    else:
        for x in test_paths:
            if not expand_and_add(x, expanded_test_paths,
                                  [package_dir, os.getcwd()]):
                expanded_test_paths.append(x)
    if withexamples:
        old_with_examples = os.environ.get('YGG_ENABLE_EXAMPLE_TESTS', None)
        os.environ['YGG_ENABLE_EXAMPLE_TESTS'] = 'True'
    argv += expanded_test_paths
    # Run test command and perform cleanup before logging any errors
    logger.info("Running %s from %s", argv, os.getcwd())
    try:
        # Set env
        old_skip_norm = os.environ.get('YGG_SKIP_COMPONENT_VALIDATION', None)
        if old_skip_norm is None:
            os.environ['YGG_SKIP_COMPONENT_VALIDATION'] = 'True'
        error_code = subprocess.call(argv)
    except BaseException:
        logger.exception('Error in running test.')
        error_code = -1
    finally:
        os.chdir(initial_dir)
        if old_skip_norm is None:
            del os.environ['YGG_SKIP_COMPONENT_VALIDATION']
        if withexamples:
            if old_with_examples is None:
                del os.environ['YGG_ENABLE_EXAMPLE_TESTS']
            else:
                os.environ['YGG_ENABLE_EXAMPLE_TESTS'] = old_with_examples
    return error_code


__all__ = []
__version__ = get_versions()['version']
del get_versions
