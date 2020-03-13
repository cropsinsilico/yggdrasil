r"""This package provides a framework for integrating models across languages
such that they can be run simultaneously, passing input back and forth."""
from yggdrasil import platform
import os
import sys
import glob
import shutil
import logging
import argparse
import subprocess
import importlib
from ._version import get_versions
from yggdrasil import config
_test_package_name = None
_test_package = None
logging.basicConfig()
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


if not os.path.isfile(config.usr_config_file):  # pragma: no cover
    from yggdrasil.languages import install_languages
    shutil.copy(config.def_config_file, config.usr_config_file)
    install_languages.install_all_languages(from_setup=True)
    config.update_language_config()


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


def run_tsts(**kwargs):  # pragma: no cover
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
        language (str, optional): Language to test. Defaults to None
            and all languages will be tested.

    """
    if '-h' not in sys.argv:
        if _test_package is None:
            raise RuntimeError("Could not locate test runner pytest or nose.")
        elif _test_package_name == 'pytest':
            test_cmd = 'pytest'
        elif _test_package_name == 'nose':
            test_cmd = 'nosetests'
        else:
            raise RuntimeError("Unsupported test package: '%s'"
                               % _test_package_name)
    parser = argparse.ArgumentParser(
        description='Run yggdrasil tests.')
    arguments = [
        (['withcoverage', 'with-coverage'], ['nocover', 'no-cover'],
         True, {'help': 'Record coverage during tests.'}),
        (['withexamples', 'with-examples'], ['noexamples', 'no-examples'],
         False, {'help': 'Run example tests when encountered.'}),
        (['longrunning', 'long-running'], ['nolongrunning', 'no-long-running'],
         False, {'help': 'Run long tests when encounterd.'}),
        (['verbose', 'v'], ['quiet'],
         True, {'help': ('Increase verbosity of output from '
                         'the test runner.')}),
        (['nocapture', 's'], ['capture'],
         True, {'help': 'Don\'t capture output from tests.'}),
        (['stop', 'x'], ['dontstop', 'dont-stop'],
         True, {'help': 'Stop after first test failure.'}),
        (['nologcapture'], ['logcapture'],
         True, {'help': ('Don\'t capture output from log '
                         'messages generated during tests.')}),
        (['validatecomponents', 'validate-components'],
         ['skipcomponentvalidation', 'skip-component-validation'],
         False,
         {'help': ('Validate components on creation. This causes '
                   'a decrease in performance so it is turned off '
                   'by default.')}),
        (['noflaky', 'no-flaky'], ['flaky'],
         False, {'help': 'Don\'t re-run flaky tests.'}),
        (['debug'], ['nodebug'],
         False, {'help': 'Turn on debug messages.'})]
    for pos_dest, neg_dest, default, kws in arguments:
        dest = pos_dest[0]
        for x in [pos_dest, neg_dest]:
            for i, y in enumerate(x):
                if len(y) == 1:
                    x[i] = '-' + y
                else:
                    x[i] = '--' + y
        if kwargs.get(dest, default):
            if kws['help'].startswith('Don\'t'):
                kws['help'].split('Don\'t', 1)[-1]
                kws['help'] = kws['help'].replace(
                    kws['help'][0], kws['help'][0].upper(), 1)
            else:
                kws['help'] = kws['help'].replace(
                    kws['help'][0], kws['help'][0].lower(), 1)
                kws['help'] = 'Don\'t ' + kws['help']
            parser.add_argument(*neg_dest, action='store_false',
                                dest=dest, **kws)
        else:
            parser.add_argument(*pos_dest, action='store_true',
                                dest=dest, **kws)
    parser.add_argument('--language', '--languages', default=[],
                        nargs="+", type=str,
                        help='Language(s) that should be tested.')
    parser.add_argument('--default-comm', '--defaultcomm', type=str,
                        help=('Comm type that default should be set '
                              'to before running tests.'))
    parser.add_argument('--ci', action='store_true',
                        help=('Perform addition operations required '
                              'for testing on continuous integration '
                              'services.'))
    suite_args = ('--test-suite', '--test-suites')
    suite_kws = dict(nargs='+', action="extend", type=str,
                     choices=['examples', 'examples_part1',
                              'examples_part2', 'types', 'timing'],
                     help='Test suite(s) that should be run.',
                     dest='test_suites')
    try:
        parser.add_argument(*suite_args, **suite_kws)
    except ValueError:
        # 'extend' introduced in 3.8
        suite_kws['action'] = 'append'
        suite_kws.pop('nargs')
        parser.add_argument(*suite_args, **suite_kws)
    args, extra_argv = parser.parse_known_args()
    initial_dir = os.getcwd()
    package_dir = os.path.dirname(os.path.abspath(__file__))
    error_code = 0
    # Peform ci tests/operations
    # Call bash script?
    if args.ci:
        extra_argv += ['-c', 'setup.cfg', '--cov-config=.coveragerc']
    # Separate out paths from options
    argv = [test_cmd]
    test_paths = []
    opt_val = 0
    for x in extra_argv:
        if opt_val > 0:
            argv.append(x)
            opt_val -= 1
        elif x.endswith('yggtest'):
            pass
        elif x.startswith('-'):
            argv.append(x)
            if (_test_package_name == 'pytest') and (x in ['-c']):
                opt_val = 1
        else:
            test_paths.append(x)
    if args.test_suites:
        for x in args.test_suites:
            if x == 'examples':
                args.withexamples = True
                test_paths.append('examples')
            elif x == 'examples_part1':
                args.withexamples = True
                test_paths.append(os.path.join(
                    'examples', 'tests', 'test_[a-g]*.py'))
            elif x == 'examples_part2':
                args.withexamples = True
                test_paths.append(os.path.join(
                    'examples', 'tests', 'test_[g-z]*.py'))
            # elif x.startswith('examples_'):
            #     args.withexamples = True
            #     test_paths.append(os.path.join(
            #         'examples', 'tests',
            #         'test_%s*.py'.format(x.split('examples_')[-1])))
            elif x == 'types':
                args.withexamples = True
                args.longrunning = True
                test_paths.append(os.path.join('examples', 'tests',
                                               'test_types.py'))
            elif x == 'timing':
                args.longrunning = True
                test_paths.append(os.path.join('tests', 'test_timing.py'))
    if _test_package_name == 'nose':
        argv += ['--detailed-errors', '--exe']
    if args.verbose:
        argv.append('-v')
    if args.nocapture:
        argv.append('-s')
    if args.stop:
        argv.append('-x')
    if args.nologcapture and (_test_package_name == 'nose'):
        argv.append('--nologcapture')
    if args.withcoverage:
        if _test_package_name == 'nose':
            argv.append('--with-coverage')
            argv.append('--cover-package=yggdrasil')
        elif _test_package_name == 'pytest':
            # See information about getting coverage of test fixtures
            # https://pytest-cov.readthedocs.io/en/stable/plugins.html
            argv.append('--cov=%s' % package_dir)
            # argv.append('--cov-append')
    if args.noflaky:
        if _test_package_name == 'pytest':
            argv += ['-p', 'no:flaky']
    else:
        if _test_package_name == 'nose':
            argv.append('--with-flaky')
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
    argv += expanded_test_paths
    # Run test command and perform cleanup before logging any errors
    logger.info("Running %s from %s", argv, os.getcwd())
    new_config = {}
    old_config = {}
    new_env = {}
    old_env = {}
    pth_file = 'ygg_coverage.pth'
    assert(not os.path.isfile(pth_file))
    try:
        # Set env
        if args.withexamples:
            new_env['YGG_ENABLE_EXAMPLE_TESTS'] = 'True'
        if args.language:
            from yggdrasil.components import import_component
            args.language = [import_component('model', x).language
                             for x in args.language]
            new_env['YGG_TEST_LANGUAGE'] = ','.join(args.language)
        if args.default_comm:
            new_env['YGG_DEFAULT_COMM'] = args.default_comm
        if args.longrunning:
            new_env['YGG_ENABLE_LONG_TESTS'] = 'True'
        if args.withcoverage:
            new_env['COVERAGE_PROCESS_START'] = 'True'
            # if _test_package_name == 'pytest':
            #     # See information about getting coverage of test fixtures
            #     # https://pytest-cov.readthedocs.io/en/stable/plugins.html
            #     new_env['COV_CORE_SOURCE'] = package_dir
            #     new_env['COV_CORE_CONFIG'] = '.coveragerc'
            #     new_env['COV_CORE_DATAFILE'] = '.coverage.eager'
            with open(pth_file, 'w') as fd:
                fd.write("import coverage; coverage.process_startup()")
        if args.debug:
            new_config[('debug', 'ygg')] = 'DEBUG'
            new_config[('debug', 'client')] = 'DEBUG'
        if args.test_suites and ('timing' in args.test_suites):
            new_env['YGG_TEST_PRODUCTION_RUNS'] = 'True'
        if not args.validatecomponents:
            new_env['YGG_SKIP_COMPONENT_VALIDATION'] = 'True'
        # Update environment and config
        for k, v in new_env.items():
            old_env[k] = os.environ.get(k, None)
            os.environ[k] = v
        for k, v in new_config.items():
            old_config[k] = config.ygg_cfg_usr.get(k[0], k[1], None)
            config.ygg_cfg_usr.set(k[0], k[1], v)
        config.ygg_cfg_usr.update_file()
        # Perform CI specific pretest operations
        if args.ci:
            top_dir = os.path.dirname(os.getcwd())
            src_cmd = ('python -c \"import versioneer; '
                       'print(versioneer.get_version())\"')
            dst_cmd = ('python -c \"import yggdrasil; '
                       'print(yggdrasil.__version__)\"')
            src_ver = subprocess.check_output(src_cmd, shell=True)
            dst_ver = subprocess.check_output(dst_cmd, shell=True,
                                              cwd=top_dir)
            if src_ver != dst_ver:  # pragma: debug
                raise RuntimeError(("Versions do not match:\n"
                                    "\tSource version: %s\n"
                                    "\tBuild  version: %s\n")
                                   % (src_ver, dst_ver))
            if os.environ.get("INSTALLR", None) == "1":
                from yggdrasil import tools
                print(tools.which("R"))
                print(tools.which("Rscript"))
            subprocess.check_call(["flake8", "yggdrasil"])
            if os.environ.get("YGG_CONDA", None):
                subprocess.check_call(["python", "create_coveragerc.py"])
            if not os.path.isfile(".coveragerc"):
                raise RuntimeError(".coveragerc file dosn't exist.")
            with open(".coveragerc", "r") as fd:
                print(fd.read())
            subprocess.check_call(["ygginfo", "--verbose"])
        error_code = subprocess.call(argv)
    except BaseException:
        logger.exception('Error in running test.')
        error_code = -1
    finally:
        os.chdir(initial_dir)
        for k, v in old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        for k, v in old_config.items():
            if v is None:
                config.ygg_cfg_usr.pop(k[0], k[1])
            else:
                config.ygg_cfg_usr.set(k[0], k[1], v)
        config.ygg_cfg_usr.update_file()
        if os.path.isfile(pth_file):
            os.remove(pth_file)
    return error_code


__all__ = []
__version__ = get_versions()['version']
del get_versions
