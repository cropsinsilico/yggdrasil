r"""This package provides a framework for integrating models across languages
such that they can be run simultaneously, passing input back and forth."""
from yggdrasil import platform
import os
import sys
import logging
import subprocess
import importlib
from ._version import get_versions
_test_package_name = None
_test_package = None
order = ['pytest', 'nose']
# order = ['nose', 'pytest']
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


def run_tsts(verbose=True, nocapture=True, stop=True,
             nologcapture=True, withcoverage=True):  # pragma: no cover
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

    """
    if _test_package is None:
        raise RuntimeError("Could not locate test runner pytest or nose.")
    elif _test_package_name == 'pytest':
        test_cmd = 'pytest'
        func_sep = '::'
    elif _test_package_name == 'nose':
        test_cmd = 'nosetests'
        func_sep = ':'
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
            # if _test_package_name == 'nose':
            #     argv.append(x)
            print(x)  # pass
        elif x == '--nocover':
            withcoverage = False
        elif x.startswith('-'):
            argv.append(x)
            if (_test_package_name == 'pytest') and (x in ['-c']):
                opt_val = 1
        else:
            test_paths.append(x)
    if _test_package_name == 'nose':
        argv += ['--detailed-errors', '--exe']
    # elif _test_package_name == 'pytest':
    #     argv.append('--ignore=yggdrasil/rapidjson/')
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
    if not test_paths:
        test_paths.append(package_dir)
    else:
        for i in range(len(test_paths)):
            if not os.path.isabs(test_paths[i]):
                for func_sep in ['::', ':']:
                    if (func_sep in test_paths[i]):
                        path, mod = test_paths[i].rsplit(func_sep, 1)
                        if (((not os.path.isabs(path))
                             and os.path.exists(os.path.join(package_dir, path)))):
                            test_paths[i] = '%s%s%s' % (
                                os.path.join(package_dir, path), func_sep, mod)
                            break
                else:
                    if os.path.exists(os.path.join(package_dir, test_paths[i])):
                        test_paths[i] = os.path.join(package_dir, test_paths[i])
    # os.chdir(package_dir)
    argv += test_paths
    print("running", argv)
    print(os.getcwd())
    try:
        error_code = subprocess.call(argv)
        # if _test_package_name == 'nose':
        #     result = _test_package.run(argv=argv)
        #     if not result:
        #         error_code = -1
        # elif _test_package_name == 'pytest':
        #     error_code = _test_package.main(argv)
        # else:
        #     raise RuntimeError("No test runner.")
    except BaseException:
        logging.exception('Error in running test.')
        error_code = -1
    finally:
        os.chdir(initial_dir)
    return error_code


__all__ = []
__version__ = get_versions()['version']
del get_versions
