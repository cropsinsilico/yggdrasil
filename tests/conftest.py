import os
import gc
import re
import sys
import glob
import copy
import shutil
import pytest
import logging
import argparse
import subprocess
import contextlib
import numpy as np
import pprint
from yggdrasil import platform, constants, rapidjson
from yggdrasil.serialize.ObjSerialize import ObjDict
from yggdrasil.serialize.PlySerialize import PlyDict
from yggdrasil.tools import (
    get_supported_lang, get_supported_comm, get_supported_type,
    resolve_language_aliases)
from yggdrasil.components import import_component
from yggdrasil.multitasking import _on_mpi
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

pytest_plugins = 'pytest-yggdrasil'
_test_directory = os.path.abspath(os.path.dirname(__file__))
_update_args_in_cmdline = False

_test_registry = []
_weakref_registry = []
_markers = [
    ("long_running", "--long-running",
     "tests that take a long time to run", None),
    ("extra_example", "--extra-examples",
     "tests for superfluous examples", None),
    ("production_run", "--production-run", None),
    ("remote_service", "--remote-service",
     "tests that must connect to a running remote service", None),
    ("serial", None,
     "tests that must be run in serial", None),
    ("subset_representative", None,
     "tests that represent a limited subset of the total tests", None),
    ("subset_rapidjson", None,
     "tests that represent a limited subset of the rapidjson submodule", None)
]
_params = {
    "example_name": [],
    "language": sorted([x for x in constants.LANGUAGES['all']
                        if x not in ['mpi', 'dummy']]),
    "commtype": sorted(get_supported_comm()),
    "filetype": sorted(list(
        constants.COMPONENT_REGISTRY["file"]["subtypes"].keys())),
    "use_async": ['False', 'True'],
    "transform": None,
    "filter": None,
    "serializer": None,
    "typename": get_supported_type(),
}
_mpi_paths = [
    os.path.join("communication", "test_MPIComm.py"),
    os.path.join("examples", "test_gs_lesson4.py"),
    os.path.join("examples", "test_rpc_lesson3b.py"),
]
if platform._is_win:
    _example1_pattern = "[a-g]*"
else:
    _example1_pattern = "[A-Za-g]*"
    _mpi_paths.append(
        os.path.join("examples", "test_model_error_with_io.py"))
_suites = [
    ("top", "tests without an explicit suite", [""], []),
    ("examples", "examples", ["examples"], []),
    ("examples_part1", "1st half of examples",
     [os.path.join("examples", f"test_{_example1_pattern}*.py")], []),
    ("examples_part2", "2nd half of examples",
     [os.path.join("examples", "test_[h-z]*.py")], []),
    ("demos", "demonstrations", ["demos"], []),
    ("types", "type I/O in the supported languages",
     [os.path.join("examples", "test_types.py")], ['--long-running']),
    ("timing", "timing statistics tools", ["test_timing.py"],
     ["--long-running", "--production-run"]),
    ("comms", "communicators", ["communication"], []),
    ("files", "file communicators", ["communication"], []),
    ("connections", "connection drivers",
     [os.path.join("drivers", "test_ConnectionDriver.py"),
      os.path.join("drivers", "test_FileInputDriver.py"),
      os.path.join("drivers", "test_FileOutputDriver.py"),
      os.path.join("drivers", "test_RPCRequestDriver.py")], []),
    ("models", "model drivers",
     [os.path.join("drivers", "test_*ModelDriver.py")], []),
    ("mpi", "MPI based communication", _mpi_paths, []),
]


class DummyParser(argparse.ArgumentParser):

    def __init__(self, isolate_options=[]):
        self.isolate_options = isolate_options
        super(DummyParser, self).__init__()
        self.add_argument("file_or_dir", nargs="*")
        self.add_argument('-c', type=str, nargs=1)
        self.add_argument('-p', type=str, nargs=1)
        add_options_to_parser(self)

    def addoption(self, *args, **kwargs):
        name = args[0].lstrip('-').replace('-', '_')
        if self.isolate_options and not (
                (name in self.isolate_options)
                or (args[0] in self.isolate_options)):
            return
        self.add_argument(*args, **kwargs)

    def parse_known_and_unknown_args(self, *args, **kwargs):
        return self.parse_known_args(*args, **kwargs)


def setup_ci(opts, disable_extra=False):
    import site
    top_dir = os.path.dirname(os.getcwd())
    for x in site.getsitepackages():
        package_dir = os.path.join(x, 'yggdrasil')
        if os.path.isdir(package_dir):
            break
    assert os.path.isdir(package_dir)
    opts += ['-v',
             '--import-mode=importlib',
             # '--import-mode=append',
             f'--cov={package_dir}',
             '--config-file=pyproject.toml',
             '--cov-config=.coveragerc',
             '--ignore=yggdrasil/rapidjson/']
    # f'--rootdir={package_dir}']
    # if not any(x.startswith('--with-mpi') for x in args):
    #     args += ['--reruns=2', '--reruns-delay=1', '--timeout=900']
    if disable_extra:
        return
    # Additional checks
    if not os.path.isfile('pyproject.toml'):
        raise RuntimeError("The CI tests must be run from the root "
                           "directory of the yggdrasil git repository.")
    try:
        import tomllib
        with open('pyproject.toml', "rb") as f:
            pyproject_data = tomllib.load(f)
    except ImportError:
        import toml as toml
        with open('pyproject.toml', "r") as f:
            pyproject_data = toml.load(f)
    git_version = pyproject_data['tool']['setuptools_scm']['git_describe_command']
    src_cmd = (
        f'python -c \"import setuptools_scm; '
        f'print(setuptools_scm.get_version('
        f'git_describe_command = \\\"{git_version}\\\"))\"')
    dst_cmd = ('python -c \"import yggdrasil; '
               'print(yggdrasil.__version__)\"')
    dir_cmd = ('python -c \"import yggdrasil; '
               'print(yggdrasil.__file__)\"')
    src_ver = subprocess.check_output(src_cmd, shell=True)
    dst_ver = subprocess.check_output(dst_cmd, shell=True, cwd=top_dir)
    src_dir = subprocess.check_output(dir_cmd, shell=True)
    dst_dir = subprocess.check_output(dir_cmd, shell=True,
                                      cwd=top_dir)
    message = (f"Versions do not match or local yggdrasil loaded:\n"
               f"\tSource version: {src_ver}\n"
               f"\tBuild  version: {dst_ver}\n"
               f"\tSource directory: {src_dir}\n"
               f"\tBuild  directory: {dst_dir}\n"
               f"\tCurr   directory: {os.getcwd()}\n"
               f"\tTop    directory: {top_dir}\n")
    if src_ver != dst_ver or src_dir == dst_dir:  # pragma: debug
        raise RuntimeError(message)
    subprocess.check_call(
        ["flake8", "yggdrasil"])  # , "--append-config", "setup.cfg"])
    if not os.path.isfile(".coveragerc"):
        raise RuntimeError(".coveragerc file dosn't exist.")
    with open(".coveragerc", "r") as fd:
        contents = fd.read()
        print(f".coveragerc (cwd={os.getcwd()}):\n{contents}")
        assert contents
    subprocess.check_call(["yggdrasil", "info", "--verbose"])


class ArgsWrapper(object):

    def __init__(self, args, options, parser):
        self.args = args
        self.options = options
        self.parser = parser
        self.modified = False
        self.orig_args = copy.deepcopy(args)
        if self.options:
            for k in ['separate_tests', 'suite', 'file_or_dir']:
                if getattr(self.options, k, None) is None:
                    setattr(self.options, k, [])

    @classmethod
    def from_config(cls, config):
        known_options = config.known_args_namespace
        assert (_test_directory == known_options._yggdrasil_tests_directory)
        args = known_options._yggdrasil_args
        parser = known_options._yggdrasil_parser
        options = config.option
        if not hasattr(options, 'end_yggdrasil_opts'):
            options = parser.parse(args)
            config.option = options
            assert hasattr(options, 'end_yggdrasil_opts')
        return cls(args, options, parser)

    def isolate_options(self, options):
        if isinstance(options, str):
            options = [options]
        parser = DummyParser(isolate_options=options)
        return parser.parse_known_and_unknown_args(self.args)

    def _group_flags(self, options):
        i = 0
        mod = []
        while i < len(options):
            x = options[i]
            if ((x.startswith('-') and (i + 1) < len(options)
                 and not options[i + 1].startswith('-'))):
                mod.append([x] + [y for y in options[(i + 1):]
                                  if not y.startswith('-')])
                i += len(x)
            else:
                mod.append(x)
                i += 1
        return mod

    def _split_flags(self, option):
        add_flags = []
        if isinstance(option, list):
            add_flags = option[1:]
            option = option[0]
            assert option.startswith('-')
        return option, add_flags

    def _norm(self, option):
        if '=' in option:
            option = option.split('=')[0]
        details = self.get_option_details(option)
        flag = details['flag']
        option = details['option']
        # if details['default'] is None:
        # if details['option'] == 'mpi_nproc':
        #     pprint.pprint(details)
        #     import pdb
        #     pdb.set_trace()
        return option, flag, details
    
    def __iadd__(self, other):
        for x in self._group_flags(other):
            self.append(x)
        return self

    def __isub__(self, other):
        for x in self._group_flags(other):
            self.remove(x)
        return self

    def find_argument(self, option):
        is_flag = option.startswith('-')
        # if not hasattr(self.parser, '_groups'):
        #     pprint.pprint(dir(self.parser))
        #     import pdb
        #     pdb.set_trace()
        for g in self.parser._groups + [self.parser._anonymous]:
            for arg in g.options:
                if (((is_flag and option in (arg._long_opts
                                             + arg._short_opts))
                     or ((not is_flag) and option == arg.dest))):
                    return arg
        raise RuntimeError(f"Could not locate an option corresponding"
                           f" to {option}")

    def get_option_details(self, option):
        arg = self.find_argument(option)
        out = {"option": arg.dest,
               "opts": arg._long_opts + arg._short_opts,
               "default": getattr(arg, 'default', None),
               "is_unique": True,
               "attr": arg._attrs,
               "arg": arg}
        out['flag'] = out['opts'][0]
        action = arg._attrs.get('action', None)
        nargs = arg._attrs.get('nargs', None)
        if action == 'store_true':
            out['default'] = False
        elif action == 'store_false':
            out['default'] = True
        elif action == 'append':
            out['default'] = []
            out['is_unique'] = False
            out['is_list'] = True
        elif nargs == '*':
            out['default'] = []
            out['is_unique'] = False
            out['is_list'] = True
        elif action == 'count':
            out['is_unique'] = False
        return out

    def update(self, args):
        self.args = args
        self.options = self.parser.parse_known_and_unknown_args(
            self.args)[0]
        self.modified = False
        self.orig_args = copy.deepcopy(args)

    def append(self, option, value=None, overwrite=False):
        add_files = []
        option, add_flags = self._split_flags(option)
        if '=' in option:
            if value is not None:
                raise ValueError("Cannot specify value in flag and value")
            option, value = option.split('=')
        option, flag, details = self._norm(option)
        default = details['default']
        if add_flags and not details.get('is_list', False):
            if option == 'end_yggdrasil_opts':
                add_files = add_flags
                add_flags = []
                print("ADD_FILES", add_files)
            else:
                raise ValueError(f"Option {option} does not allow for "
                                 f"multiple values:\n"
                                 f"{pprint.pformat(details)}")
        if value is not None:
            if flag.startswith('--'):
                flag += f"={value}"
            else:
                add_flags.insert(0, value)
        if not (details['is_unique'] and flag in self.args):
            self.modified = True
            self.args += [flag] + add_flags
        if add_files:
            self.modified = True
            self.args += add_files
        if not self.options:
            return
        if value is None:
            value = True
        is_list = details.get(
            'is_list',
            isinstance(getattr(self.options, option, None), list))
        if not (overwrite
                or getattr(self.options, option, default) == default
                or getattr(self.options, option, default) == value):
            if is_list:
                if getattr(self.options, option) is None:
                    setattr(self.options, option, [])
            elif details['attr'].get('action', None) == 'count':
                value = getattr(self.options, option) + 1
            else:
                raise ValueError(f"Setting this option ({option}) to"
                                 f" {value} will overwrite existing"
                                 f" non-default"
                                 f" {getattr(self.options, option)}")
        if is_list:
            value = [value]
        if is_list and not overwrite:
            self.modified = True
            dst = getattr(self.options, option)
            dst += value
        else:
            self.modified = True
            setattr(self.options, option, value)
        if add_files:
            self.modified = True
            self.options.file_or_dir += add_files

    def remove_args(self, options, remove_file_or_dir=False):
        assert not self.options
        parsed_args, remaining = self.isolate_options(options)
        if not remove_file_or_dir:
            remaining += parsed_args.file_or_dir
        if len(self.args) == len(remaining) and self.args == remaining:
            return
        self.modified = True
        args_copy = copy.copy(self.args)
        self.args.clear()
        self.args += [x for x in args_copy if x in remaining]

    def remove(self, option, remove_file_or_dir=False):
        option, add_flags = self._split_flags(option)
        option, flag, details = self._norm(option)
        parsed_args, remaining = self.isolate_options(option)
        if not remove_file_or_dir:
            remaining += parsed_args.file_or_dir
        if len(self.args) == len(remaining) and self.args == remaining:
            return
        self.modified = True
        args_copy = copy.copy(self.args)
        self.args.clear()
        self.args += [x for x in args_copy if x in remaining]
        if not self.options:
            return
        setattr(self.options, option, details['default'])


def do_yggdrasil_mods(opts, dont_exit=False):
    run_process = False
    prefix = []
    prefix_pytest = ['pytest']
    # prefix_pytest = ['python', '-m', 'pytest']
    options = opts.options
    options.yggdrasil_tests_rootdir = _test_directory
    # Disable output capture
    if options.nocapture:
        opts.remove('nocapture')
        opts += ['--capture=no', '-o', 'log_cli=true']
    # MPI script
    mpi_nproc = options.mpi_nproc
    if options.mpi_nproc > 1:
        opts.remove('mpi_nproc')
    if options.mpi_script:
        mpi_test_args = [
            '--suite=mpi', f'--write-script={options.mpi_script}']
        opts.remove('mpi_script')
        if mpi_nproc > 1:
            mpi_test_args.append(f'--mpi-nproc={mpi_nproc}')
            mpi_nproc = 1  # Prevent calling remaining args with mpi
        mpi_test_args = " ".join(mpi_test_args)
        opts.append('separate_tests', mpi_test_args)
    # MPI process should be started
    if ('mpi' in options.suite) and (mpi_nproc <= 1) and (not _on_mpi):
        mpi_nproc = 2
    if mpi_nproc > 1:
        run_process = True
        prefix = ['mpiexec', '-n', str(mpi_nproc)]
        print(f"mpi_flavor = {mpi_flavor()}")
        if ((os.environ.get('CI', False) and platform._is_linux
             and mpi_flavor() == 'openmpi')):
            prefix.append('--oversubscribe')
        opts.append('--with-mpi')
        opts += ['-p', 'no:flaky']
        opts -= ['--reruns=2', '--reruns-delay=1', '--timeout=900']
    # Continuous integration
    if options.ci and (not _on_mpi):
        setup_ci(opts)
        opts.args.remove('--ci')  # Much faster
        # Must launch in separate process so that pytest recognizes
        # the added --cov={install_dir} and --import-mode flags
        run_process = True
    # Write a script to call later
    if options.write_script:
        print(f"Writing script to call tests {options.write_script}")
        write_script = options.write_script
        opts.remove('write_script')
        if not os.path.isabs(write_script):
            write_script = os.path.abspath(write_script)
        write_pytest_script(write_script,
                            prefix + prefix_pytest + opts.args)
        opts.remove('write_script')
        if dont_exit:
            return 0
        sys.exit(0)
    # Check for separate tests
    separate_tests = options.separate_tests
    if options.separate_tests:
        opts.remove('separate_tests')
    for x in separate_tests:
        opts_copy = ArgsWrapper(copy.copy(opts.args), False, opts.parser)
        excluded = ([m[1] for m in _markers if m[1]]
                    + ['suite', 'language', 'skip_language', 'default_comm']
                    + [f'parametrize_{k}' for k in _params.keys()])
        opts_copy.remove_args(excluded, remove_file_or_dir=True)
        opts_copy.update(x.split() + opts_copy.args)
        # x_args_keys = [k.split('=')[0] for k in opts_copy.args
        #                if k.startswith('-')]
        # for k in x_args_copy:
        #     if k.split('=')[0] not in x_args_keys:
        #         x_args.append(k)
        assert (any((k.split('=', 1)[0] == '--write-script')
                    for k in opts_copy.args))
        if not options.second_attempt:
            do_yggdrasil_mods(opts_copy, dont_exit=True)
    # Run test in separate process
    if run_process:
        print(f"Calling subprocess: {prefix + prefix_pytest + opts.args}")
        flag = subprocess.call(prefix + prefix_pytest + opts.args)
        if dont_exit:
            return flag
        sys.exit(flag)
    # Add test suites paths
    suite_map = {x[0]: (x[2], x[3]) for x in _suites}
    suite_files = []
    for suite in options.suite:
        for f in suite_map[suite][0]:
            suite_files += glob.glob(os.path.join(_test_directory, f))
        opts += suite_map[suite][1]
    opts._norm('--suite')
    if suite_files:
        if not options.file_or_dir:
            opts += ['--end-yggdrasil-opts'] + sorted(suite_files)
    elif not options.file_or_dir:
        opts += ['--end-yggdrasil-opts'] + [_test_directory]
    print(f"Update paths: {options.file_or_dir}")
    print(f"Updated args: {opts.args}")
    # if opts.modified:
    #     print(f"Arguments modified, so tests will be run in an"
    #           f" external process:\n"
    #           f"  old: {opts.orig_args}\n"
    #           f"  new: {opts.args}")
    #     flag = subprocess.call(prefix_pytest + opts.args)
    #     assert flag
    #     sys.exit(flag)


def pytest_addoption(parser):
    add_options_to_parser(parser)


def add_options_to_parser(parser):
    languages = sorted(get_supported_lang())
    for x in _markers:
        if not x[1]:
            continue
        parser.addoption(x[1], action="store_true", default=False,
                         help=f"run {x[2]} tests")
    for k, v in _params.items():
        if v is None:
            v = sorted(list(constants.COMPONENT_REGISTRY[k]["subtypes"].keys()))
        choices = v if v else None
        parser.addoption(f"--parametrize-{k.replace('_', '-')}",
                         help=f"Set '{k}' test parameter", nargs='*',
                         choices=choices)
    parser.addoption('--second-attempt', action='store_true',
                     help=('Indicates the is the second attempt.'))
    parser.addoption('--ci', action='store_true',
                     help=('Perform additional operations required for '
                           'testing on continuous integration services.'))
    parser.addoption('--ygg-debug', action='store_true',
                     help=('Turn on debug level logging and increase the '
                           'scrutiny of messages during testing.'))
    parser.addoption('--ygg-loglevel', '--ygg-log-level', type=str,
                     help='Level of logging to use.')
    parser.addoption('--default-comm', type=str,
                     choices=sorted(
                         constants.COMPONENT_REGISTRY['comm']['subtypes'].keys()),
                     help="Communicator that should be used by default.")
    parser.addoption('--suite', '--suites', '--test-suite',
                     # type=str, action="extend",  # python >= 3.8
                     nargs='*', choices=[x[0] for x in _suites],
                     help="Test suite that should be run.")
    parser.addoption('--language', '--languages',
                     # type=str, action="extend",  # python >= 3.8
                     nargs='*', choices=languages,
                     help="Language(s) that should be tested.")
    parser.addoption('--skip-language', '--skip-languages',
                     # type=str, action="extend",  # python >= 3.8
                     nargs='*', choices=languages,
                     help="Language(s) that should be tested.")
    parser.addoption('--write-script', type=str,
                     help=("Name of script that should be created to run "
                           "tests."))
    parser.addoption('--mpi-nproc', type=int, default=1,
                     help="Number of MPI processes to run tests on.")
    parser.addoption('--mpi-script', type=str,
                     help=("Name of script that should be written to "
                           "run MPI tests. If --mpi-nproc is not set, it "
                           "will default to 2. If --mpi-nproc is set, it "
                           "will only be used in the MPI script that is "
                           "generated."))
    parser.addoption('--separate-tests', '--separate-test',
                     type=str, action="append",
                     help="Flags for an additional test that should be run")
    parser.addoption('--nocapture', action="store_true",
                     help="Don't capture output or log messages from tests.")
    parser.addoption('--end-yggdrasil-opts', action="store_true",
                     help="Internal use only")
    parser.addoption('--rerun-flaky', action="store_true",
                     help="Re-run flaky tests.")


if _update_args_in_cmdline:
    def pytest_cmdline_preparse(config, args):
        opts = ArgsWrapper.from_config(config)
        do_yggdrasil_mods(opts)


def pytest_cmdline_main(config):
    r"""Adjust the pytest arguments before testing."""
    # Check for run in separate process before adding CI args
    if not _update_args_in_cmdline:
        opts = ArgsWrapper.from_config(config)
        do_yggdrasil_mods(opts)


def pytest_configure(config):
    # Add markers to configuration
    for x in _markers:
        config.addinivalue_line("markers", f"{x[0]}: {x[2]}")
    config.addinivalue_line(
        "markers", ("suite(name,disabled=False,ignore=[]): mark test "
                    "as belonging to a group of tests, whether or not the "
                    "suite should be disabled by default, and suites "
                    "included by parent classes that should be ignored"))
    config.addinivalue_line(
        "markers", ("language(name): mark test as requiring a language is "
                    "installed"))
    config.addinivalue_line(
        "markers", ("absent_language(name): mark test as requiring a "
                    "language is NOT installed."))
    config.addinivalue_line(
        "markers", ("related_language(name): mark test as being related "
                    "to a language. The language may or may not be "
                    "installed, but must be enabled for the test to run."))
    config.addinivalue_line(
        "markers", ("flaky_optin(name,condition=None,reruns=1,"
                    "reruns_delay=0): mark test as "
                    "flaky without automatically re-running on "
                    "failure unless --rerun-flaky is specified."))


# def pytest_runtest_setup(item):
#     langs = [mark.args[0] for mark in item.iter_markers(name="language")]
#     if langs:
#         enabled = item.config.getoption("--language")
#         disabled = item.config.getoption("--skip-language")
#         if (((enabled and (not all(x in enabled for x in langs)))
#              or (disabled and any(x in disabled for x in langs)))):
#             pytest.skip(f"test requires languages {langs!r}")
#         elif not all(import_component('model', x).is_installed()
#                      for x in langs):
#             pytest.skip(f"test requires languages {langs!r}, "
#                         f"not all are installed")
#     absent_langs = [mark.args[0] for mark in
#                     item.iter_markers(name="absent_language")]
#     if absent_langs:
#         if any(import_component('model', x).is_installed()
#                for x in absent_langs):
#             pytest.skip(f"test requires languages {absent_langs!r} NOT "
#                         f"be installed")


def pytest_collection_modifyitems(config, items):
    active_markers = config.getoption('-m')
    compiledMarkExpr = None
    if active_markers:
        from _pytest.mark.expression import Expression
        compiledMarkExpr = Expression.compile(active_markers)
    _marker_names = [x[0] for x in _markers]
    
    def check_item_enabled(item, markers=None):
        if not compiledMarkExpr:
            return False
        if markers is None:
            markers = _marker_names
        item_markers = [x.name for x in item.iter_markers()
                        if x.name in markers]
        return compiledMarkExpr.evaluate(lambda x: x in item_markers)
    
    for x in _markers:
        if (not x[1]) or config.getoption(x[1]):
            continue
        skip_x = pytest.mark.skip(reason=f"need {x[1]} to run")
        for item in items:
            if x[0] in item.keywords and not check_item_enabled(item):
                item.add_marker(skip_x)
    # Handle suite & language markers
    selected_suites = config.getoption('--suite')
    enabled = config.getoption("--language")
    disabled = config.getoption("--skip-language")
    rerun_flaky = config.getoption("--rerun-flaky")
    for item in items:
        # Suites
        suites = [mark.args[0] for mark in item.iter_markers(name="suite")]
        for mark in item.iter_markers(name="suite"):
            ignore = mark.kwargs.get('ignore', [])
            if isinstance(ignore, str):
                ignore = [ignore]
            for suite in ignore:
                while suite in suites:
                    suites.remove(suite)
        if 'examples' in suites:
            example_name = item.listnames()[-1].split('[')[-1].split('-')[0]
            if re.match(_example1_pattern, example_name):
                suites.append('examples_part1')
            else:
                suites.append('examples_part2')
        if check_item_enabled(item):
            suites_disabled = []
        else:
            suites_disabled = [mark.kwargs.get('disabled', False)
                               for mark in item.iter_markers(name="suite")]
        if suites and not any(suites_disabled):
            suites.append('top')
        skip_x = None
        if selected_suites:
            if (((suites and not any(x in selected_suites for x in suites))
                 or (not suites and ('top' not in selected_suites)))):
                skip_x = pytest.mark.skip(
                    reason=f"none of test's suites ({suites}) selected.")
        elif any(suites_disabled):
            skip_x = pytest.mark.skip(
                reason=f"one of test's suites ({suites}) not selected.")
        if skip_x:
            item.add_marker(skip_x)
        # Selected/installed languages
        langs = [mark.args[0] for mark in item.iter_markers(name="language")]
        if langs:
            skip_x = None
            if (((enabled and (not all(x in enabled for x in langs)))
                 or (disabled and any(x in disabled for x in langs)))):
                skip_x = pytest.mark.skip(
                    reason=f"test requires languages {langs!r}")
            elif not all(import_component('model', x).is_installed()
                         for x in langs):
                skip_x = pytest.mark.skip(
                    reason=(f"test requires languages {langs!r}, "
                            f"not all are installed"))
            if skip_x:
                item.add_marker(skip_x)
        # Related languages
        related_langs = [mark.args[0] for mark in
                         item.iter_markers(name="related_language")]
        if related_langs:
            if (((enabled and (not all(x in enabled for x in related_langs)))
                 or (disabled and any(x in disabled for x in related_langs)))):
                item.add_marker(
                    pytest.mark.skip(
                        reason=(f"test is related to one or more languages "
                                f"{langs!r} that are not enabled or are "
                                f"disabled")))
        # Excluded languages
        absent_langs = [mark.args[0] for mark in
                        item.iter_markers(name="absent_language")]
        if absent_langs:
            if any(import_component('model', x).is_installed()
                   for x in absent_langs):
                item.add_marker(
                    pytest.mark.skip(
                        reason=(f"test requires languages {absent_langs!r} "
                                f"NOT be installed")))
        # Flaky markers
        if rerun_flaky:
            for mark in item.iter_markers(name="flaky_optin"):
                item.add_marker(
                    pytest.mark.flaky(*mark.args, **mark.kwargs))


def pytest_generate_tests(metafunc):
    for k, v in _params.items():
        if k not in metafunc.fixturenames:
            continue
        fixture = getattr(metafunc.cls, k, None)
        if ((fixture
             and ('request' not in
                  fixture.__wrapped__.__code__.co_varnames))):
            continue
        flag = f"--parametrize-{k.replace('_', '-')}"
        scope = None
        class_params = None
        if metafunc.cls and hasattr(metafunc.cls, f"parametrize_{k}"):
            class_params = getattr(metafunc.cls, f"parametrize_{k}")
            if callable(class_params):
                class_params = class_params(metafunc)
        if metafunc.config.getoption(flag):
            params = metafunc.config.getoption(flag)
            if k == 'use_async':
                params = [(x.lower() in ['true', '1']) for x in params]
            if isinstance(class_params, (list, tuple)):
                params = [x for x in params if x in class_params]
        elif isinstance(class_params, (list, tuple)):
            params = class_params
            scope = "class"
        else:
            if metafunc.cls:
                scope = "class"
            else:
                scope = None
            if v is None:
                params = sorted(list(
                    constants.COMPONENT_REGISTRY[k]["subtypes"].keys()))
            else:
                params = v
        metafunc.parametrize(k, params, indirect=True, scope=scope)


def write_pytest_script(fname, argv):
    r"""Write a script to run the pytest command.

    Args:
        fname (str): Full path to file where the script should be written.
        argv (list): Command options.

    """
    import stat
    from yggdrasil import platform
    cmd = ' '.join(argv)
    if platform._is_win:
        cmd = cmd.replace('\\', '/')
    if platform._is_win and (not os.environ.get("CONDA_PREFIX", None)):
        lines = [cmd + ' %*']
    else:
        lines = ['#!/bin/bash',
                 cmd + ' $@']
    with open(fname, 'w') as fd:
        fd.write('\n'.join(lines))
    os.chmod(fname, (stat.S_IRWXU
                     | stat.S_IRGRP | stat.S_IXGRP
                     | stat.S_IROTH | stat.S_IXOTH))
    contents = '\n\t' + '\n\t'.join(lines)
    print(f"Wrote test script to '{fname}':{contents}")


# Session level constants
@pytest.fixture(scope="session",
                params=[pytest.param(0, marks=pytest.mark.serial)])
def serial():
    r"""Test must be run in serial."""
    pass


@pytest.fixture(scope="session")
def project_dir():
    r"""Directory in which yggdrasil is installed."""
    import yggdrasil
    return os.path.abspath(os.path.dirname(yggdrasil.__file__))


@pytest.fixture(scope="session")
def logger():
    r"""Package logger."""
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    return logger


@pytest.fixture(scope="session")
def MagicTestError():
    class MagicTestError(Exception):
        r"""Special exception for testing."""
        pass
    return MagicTestError


@pytest.fixture(scope="session")
def magic_error_replacement(MagicTestError):
    r"""Replacement for monkeypatching to raise an error."""
    def magic_error_replacement_w(*args, **kwargs):
        raise MagicTestError()
    return magic_error_replacement_w


@pytest.fixture(scope="session")
def timeout():
    r"""Time that should be waited during time outs."""
    return 10.0


@pytest.fixture(scope="session")
def polling_interval():
    r"""Time that should be waited between polls during time outs."""
    return 0.01


@pytest.fixture(scope="session")
def communicator_types():
    r"""list: Supported communicator types."""
    from yggdrasil.tools import get_supported_comm
    return get_supported_comm()


@pytest.fixture(scope="session")
def languages():
    r"""list: Supported languages."""
    from yggdrasil.tools import get_supported_lang
    return get_supported_lang()


@pytest.fixture(scope="session")
def testdir():
    r"""Test directory."""
    return _test_directory


@pytest.fixture(scope="session")
def scripts(testdir):
    r"""Dictionary of test scripts for each language."""
    from yggdrasil import tools
    script_dir = os.path.join(testdir, 'scripts')
    script_list = [
        ('c', ['gcc_model.c', 'hellofunc.c']),
        ('c++', ['gcc_model.cpp', 'hellofunc.c']),
        ('make', 'gcc_model'),
        ('cmake', 'gcc_model'),
        ('matlab', 'matlab_model.m'),
        ('matlab_error', 'matlab_error_model.m'),
        ('python', 'python_model.py'),
        ('error', 'error_model.py'),
        ('lpy', 'lpy_model.lpy'),
        ('r', 'r_model.R'),
        ('fortran', ['hellofunc.f90', 'fortran_model.f90']),
        ('sbml', 'sbml_model.xml'),
        ('osr', 'osr_model.xml'),
        ('julia', 'julia_model.jl'),
        ('pytorch', 'pytorch_model.py')]
    scripts = {}
    for k, v in script_list:
        if isinstance(v, list):
            scripts[k] = [os.path.join(script_dir, iv) for iv in v]
        else:
            scripts[k] = os.path.join(script_dir, v)
    # scripts = {k: os.path.join(script_dir, v) for k, v in script_list}
    if platform._is_win and (not tools.in_powershell()):  # pragma: windows
        scripts['executable'] = ['ping', '-n', '1', '127.0.0.1']
    else:
        scripts['executable'] = ['sleep', 0.1]
    # Makefile
    if platform._is_win:  # pragma: windows
        makefile0 = os.path.join(script_dir, "Makefile_windows")
    else:
        makefile0 = os.path.join(script_dir, "Makefile_linux")
    dest = os.path.join(script_dir, "Makefile")
    shutil.copy(makefile0, dest)
    yield scripts
    if os.path.isfile(dest):
        os.remove(dest)


@pytest.fixture(scope="session")
def yamls(testdir):
    r"""Dictionary of test YAMLs for each language."""
    yaml_dir = os.path.join(testdir, 'yamls')
    yaml_list = [
        ('c', 'gcc_model.yml'),
        ('cpp', 'gpp_model.yml'),
        ('make', 'make_model.yml'),
        ('cmake', 'cmake_model.yml'),
        ('matlab', 'matlab_model.yml'),
        ('python', 'python_model.yml'),
        ('error', 'error_model.yml'),
        ('lpy', 'lpy_model.yml'),
        ('fortran', 'fortran_model.yml'),
        ('sbml', 'sbml_model.yml'),
        ('osr', 'osr_model.yml')]
    yamls = {k: os.path.join(yaml_dir, v) for k, v in yaml_list}
    return yamls


# Fixtures based on CLI options
@pytest.fixture(scope="session", autouse=True)
def config_env(pytestconfig):
    r"""Set environment variables based on CLI options."""
    second_attempt = pytestconfig.getoption("--second-attempt")
    production_run = pytestconfig.getoption("--production-run")
    default_comm = pytestconfig.getoption("--default-comm")
    debug = pytestconfig.getoption("--ygg-debug")
    loglevel = pytestconfig.getoption("--ygg-loglevel")
    if second_attempt:
        production_run = False
        debug = True
    if pytestconfig.getoption("--rerun-flaky"):
        os.environ['YGGDRASIL_RERUN_FLAKY'] = '1'
    from yggdrasil import config
    with config.temp_config(production_run=production_run,
                            debug=debug, default_comm=default_comm,
                            loglevel=loglevel, client_loglevel=loglevel):
        config.cfg_logging()
        yield
    config.cfg_logging()
    

# Fixtures for managing the test environment
@pytest.fixture(scope="session", autouse=True)
def utf8_encoding():
    r"""Set the encoding to utf-8 if it is not already."""
    lang = os.environ.get('LANG', '')
    if 'UTF-8' not in lang:  # pragma: debug
        os.environ['LANG'] = 'en_US.UTF-8'
    yield
    if 'UTF-8' not in lang:  # pragma: debug
        os.environ['LANG'] = lang


@pytest.fixture(scope="session")
def debug_log():
    r"""Set the log level to debug."""
    from yggdrasil.config import ygg_cfg, cfg_logging
    loglevel = ygg_cfg.get('debug', 'ygg')
    ygg_cfg.set('debug', 'ygg', 'DEBUG')
    cfg_logging()
    yield
    if loglevel is not None:
        ygg_cfg.set('debug', 'ygg', loglevel)
        cfg_logging()


@pytest.fixture(scope="session")
def change_default_comm():
    r"""Set the default comm."""
    @contextlib.contextmanager
    def change_default_comm_w(default_comm):
        from yggdrasil.communication.DefaultComm import DefaultComm
        old_default_comm = os.environ.get('YGG_DEFAULT_COMM', None)
        if default_comm is None:
            os.environ.pop('YGG_DEFAULT_COMM', None)
        else:
            os.environ['YGG_DEFAULT_COMM'] = default_comm
        DefaultComm._reset_alias()
        yield
        del os.environ['YGG_DEFAULT_COMM']
        if old_default_comm is not None:
            os.environ['YGG_DEFAULT_COMM'] = old_default_comm
        DefaultComm._reset_alias()
    return change_default_comm_w


def get_service_manager_skips(service_type, partial_commtype=None,
                              check_running=False):
    r"""Create a list of conditions and skip messages."""
    from yggdrasil.tools import is_comm_installed
    from yggdrasil.services import create_service_manager_class
    out = []
    if partial_commtype is not None:
        out.append(
            (not is_comm_installed(partial_commtype, language='python'),
             f"Communicator type '{partial_commtype}' not installed."))
    cls = create_service_manager_class(service_type=service_type)
    out.append(
        (not cls.is_installed(),
         f"Service type '{service_type}' not installed."))
    assert not check_running
    # if check_running and cls.is_installed():
    #     cli = IntegrationServiceManager(service_type=service_type,
    #                                     commtype=partial_commtype,
    #                                     for_request=True)
    #     out.append(
    #         (not cli.is_running,
    #          f"Service of type {service_type} not running."))
    return out


@pytest.fixture(scope="session")
def check_service_manager_settings():
    r"""Check that the requested settings are available, skipping if not."""
    def check_service_manager_settings_w(service_type, partial_commtype=None):
        skips = get_service_manager_skips(service_type,
                                          partial_commtype=partial_commtype)
        for s in skips:
            if s[0]:
                pytest.skip(s[1])
    return check_service_manager_settings_w


@pytest.fixture(scope="session")
def running_service(pytestconfig, check_service_manager_settings,
                    project_dir):
    r"""Context manager to run and clean-up an integration service."""
    manager = pytestconfig.pluginmanager
    plugin_class = manager.get_plugin('pytest_cov').CovPlugin
    with_coverage = False
    for x in manager.get_plugins():
        if isinstance(x, plugin_class):
            with_coverage = True
            break

    @contextlib.contextmanager
    def running_service_w(service_type, partial_commtype=None,
                          track_memory=False, debug=False):
        from yggdrasil.services import (
            IntegrationServiceManager)
        if ((((service_type, partial_commtype) == ('flask', 'rmq'))
             and platform._is_win)):
            pytest.skip("excluded on windows")
        check_service_manager_settings(service_type, partial_commtype)
        model_repo = "https://github.com/cropsinsilico/yggdrasil_models_test/models"
        log_level = logging.ERROR
        args = [sys.executable, "-m", "yggdrasil", "integration-service-manager",
                f"--service-type={service_type}"]
        if partial_commtype is not None:
            args.append(f"--commtype={partial_commtype}")
        args += ["start", f"--model-repository={model_repo}",
                 f"--log-level={log_level}"]
        if track_memory:
            args.append("--track-memory")
        if debug:
            args.append("--debug")
        process_kws = {}
        if with_coverage:
            script_path = os.path.expanduser(os.path.join('~', 'run_server.py'))
            process_kws['cwd'] = project_dir
            if platform._is_win:  # pragma: windows
                process_kws['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
            opts = []
            if service_type is not None:
                opts.append(f'service_type=\'{service_type}\'')
            if partial_commtype is not None:
                opts.append(f'commtype=\'{partial_commtype}\'')
            opts.append(f'debug={debug}')
            lines = [
                "from yggdrasil.services import IntegrationServiceManager",
                f"srv = IntegrationServiceManager({', '.join(opts)})",
                'assert not srv.is_running',
                f'srv.start_server(with_coverage={with_coverage},',
                f'                 log_level={log_level},',
                f'                 model_repository=\'{model_repo}\',',
                f'                 track_memory={track_memory})']
            with open(script_path, 'w') as fd:
                fd.write('\n'.join(lines))
            args = [sys.executable, script_path]
            # args = 'ulimit -v 256000; ' + ' '.join(args)
            # process_kws['shell'] = True
        verify_flask = (service_type == 'flask')
        if verify_flask:
            # Flask is the default, verify that it is selected
            service_type = None
        cli = IntegrationServiceManager(service_type=service_type,
                                        commtype=partial_commtype,
                                        for_request=True)
        if verify_flask:
            assert cli.service_type == 'flask'
        assert not cli.is_running
        p = subprocess.Popen(args, **process_kws)
        try:
            cli.wait_for_server()
            yield cli
            cli.stop_server()
            assert not cli.is_running
            p.wait(10)
        finally:
            if p.returncode is None:  # pragma: debug
                p.terminate()
            if with_coverage:
                if os.path.isfile(script_path):
                    os.remove(script_path)
    return running_service_w


# Utility fixtures
@pytest.fixture(scope="session")
def wait_on_function(timeout, polling_interval):
    r"""Wait on a function to time out."""
    from yggdrasil.multitasking import wait_on_function

    def wrapped_wait_on_function(*args, **kwargs):
        kwargs.setdefault("timeout", timeout)
        kwargs.setdefault("polling_interval", polling_interval)
        return wait_on_function(*args, **kwargs)
    return wrapped_wait_on_function


@pytest.fixture
def run_once(request):
    r"""Fixture indicating that the test should only be run once."""
    key = (request.cls, request.function.__name__)
    if key in _test_registry:
        pytest.skip(f"{request.cls.__name__}.{request.function.__name__} "
                    f"already ran")
    _test_registry.append(key)


@pytest.fixture
def pprint_diff():
    r"""Get the diff between the pprint.pformat string for two objects."""
    def pprint_diff_w(x, y):
        import difflib
        from yggdrasil import tools
        tools.print_encoded('\n'.join(difflib.ndiff(
            pprint.pformat(x).splitlines(),
            pprint.pformat(y).splitlines())))
    return pprint_diff_w


@pytest.fixture(scope="session")
def check_required_languages(pytestconfig):
    r"""Check if a set of languages is enabled/disabled."""
    enabled = resolve_language_aliases(
        pytestconfig.getoption("--language"))
    disabled = resolve_language_aliases(
        pytestconfig.getoption("--skip-language"))

    def check_required_languages_w(required_languages):
        required_languages = resolve_language_aliases(
            required_languages)
        if enabled and (not all(x in enabled for x in required_languages)):
            pytest.skip(f"One or more required languages "
                        f"({required_languages}) not enabled")
        if disabled and any(x in disabled for x in required_languages):
            pytest.skip(f"One or more required languages "
                        f"({required_languages}) disabled")
        for x in required_languages:
            drv = import_component('model', x)
            if not drv.is_installed():
                pytest.skip(f"{x} language not installed")
    return check_required_languages_w


@pytest.fixture(scope="session")
def check_required_comms(on_mpi):
    r"""Check if a set of comms is installed."""
    from yggdrasil.components import import_component

    def check_required_comms_w(required_comms, language="python"):
        if isinstance(required_comms, str):
            required_comms = [required_comms]
        for x in required_comms:
            comm = import_component('comm', x)
            if not comm.is_installed(language=language):
                pytest.skip(f"{x} communicator not installed for "
                            f"{language} language")
            if comm._commtype == 'mpi' and (not on_mpi):
                pytest.skip("MPI communicator requires an MPI process")
    return check_required_comms_w


@pytest.fixture(scope="class")
def recv_message_list(timeout, wait_on_function, nested_approx):
    r"""Continue receiving from a receive instance until flag is False
    (or an empty messages is received and break_on_empty is True). On
    receipt of a False flag, the recieved message is checked against the
    EOF message.

    Args:
        recv_inst (yggdrasil.communication.CommBase.CommBase): Comm
            instance that should be received from.
        expected_result (list, optional): A list of messages that the
            recieved messages should be compared against. Defaults to None
            and is ignored.
        break_on_empty (bool, optional): If True, messages will stop being
            received from the communication instance when an empty message
            is received. Defaults to False.

    Returns:
       list: Received messages.

    """
    def wrapped_recv_message_list(recv_inst, expected_result=None,
                                  break_on_empty=False):
        r"""Continue receiving until flag is False."""
        msg_list = []

        def recv_element():
            if recv_inst.is_closed:
                return True
            flag, msg_recv = recv_inst.recv(timeout)
            if flag:
                if break_on_empty and recv_inst.is_empty_recv(msg_recv):
                    return True
                msg_list.append(msg_recv)
            else:
                assert msg_recv == recv_inst.eof_msg
            return (not flag)
        wait_on_function(recv_element, timeout=timeout)
        if expected_result is not None:
            try:
                assert nested_approx(expected_result) == msg_list
            except BaseException:
                print("EXPECTED:")
                print(expected_result)
                print("ACTUAL:")
                print(msg_list)
                raise
        return msg_list
    return wrapped_recv_message_list


@pytest.fixture(scope="session")
def assert_equal_file_contents():
    r"""Assert that the contents of two files are equivalent.

    Args:
        a (object): Contents of first file for comparison.
        b (object): Contents of second file for comparison.

    Raises:
        AssertionError: If the contents are not equal.

    """
    import difflib

    def assert_equal_file_contents_w(a, b):
        if a != b:  # pragma: debug
            odiff = '\n'.join(list(difflib.Differ().compare(a, b)))
            raise AssertionError(('File contents do not match expected '
                                  'result Diff:\n%s') % odiff)
    return assert_equal_file_contents_w


@pytest.fixture(scope="session")
def check_file_exists(wait_on_function):
    r"""Check that a file exists.

    Args:
        fname (str): Full path to the file that should be checked.
        timeout (float, optional): Time that should be waited when checking
            the file's existance. Defaults to 2.

    """
    def check_file_exists_w(fname, timeout=2):
        wait_on_function(lambda: os.path.isfile(fname), timeout=timeout,
                         on_timeout=f"File '{fname}' does not exist")
    return check_file_exists_w


@pytest.fixture(scope="session")
def check_file_size(wait_on_function):
    r"""Check that file is the correct size.

    Args:
        fname (str): Full path to the file that should be checked.
        fsize (int): Size that the file should be in bytes.
        timeout (float, optional): Time that should be waited when checking
            the file size. Defaults to 2.

    """
    def check_file_size_w(fname, fsize, timeout=2):
        result = None
        if isinstance(fsize, (bytes, str)):
            result = fsize
            fsize = len(result)

        def on_timeout():  # pragma: debug
            if (result is not None) and (fsize < 200):
                print(f"Expected:\n{result}\n"
                      f"Actual:\n{open(fname, 'r').read()}")
            raise AssertionError(f"File size ({os.stat(fname).st_size}), "
                                 f"dosn't match expected size ({fsize}).")
        wait_on_function(lambda: os.stat(fname).st_size == fsize,
                         timeout=timeout, on_timeout=on_timeout)
    return check_file_size_w


@pytest.fixture(scope="session")
def check_file_contents(assert_equal_file_contents):
    r"""Check that the contents of a file are correct.

    Args:
        fname (str): Full path to the file that should be checked.
        result (str): Contents of the file.

    """
    def check_file_contents_w(fname, result):
        ocont = open(fname, 'r').read()
        assert_equal_file_contents(ocont, result)
    return check_file_contents_w


@pytest.fixture(scope="session")
def check_file(check_file_exists, check_file_size, check_file_contents):
    r"""Check that a file exists, is the correct size, and has the correct
    contents.

    Args:
        fname (str): Full path to the file that should be checked.
        result (str): Contents of the file.

    """
    def check_file_w(fname, result):
        check_file_exists(fname)
        check_file_size(fname, len(result))
        check_file_contents(fname, result)
    return check_file_w


# Equality fixtures
@pytest.fixture(scope="session")
def pandas_equality():
    r"""Comparison operation for pandas DataFrames."""
    def pandas_equality_w(a, b):
        return a.equals(b)
    return pandas_equality_w


@pytest.fixture
def pandas_equality_patch(monkeypatch, pandas_equality):
    r"""Patch pandas DataFrame so that equals is used instead of '=='"""
    import pandas
    with monkeypatch.context() as m:
        m.setattr(pandas.DataFrame, '__eq__', pandas_equality)
        yield


@pytest.fixture(scope="session")
def functions_equality():
    def functions_equality_w(a, b):
        a_str = f"{a.__module__}.{a.__name__}"
        b_str = f"{b.__module__}.{b.__name__}"
        if not (a_str.endswith(b_str) or b_str.endswith(a_str)):
            return False
        return a.__dict__ == b.__dict__
    return functions_equality_w


@pytest.fixture(scope="session")
def nested_approx(patch_equality, pandas_equality):
    r"""Nest pytest.approx for assertion."""
    from collections import OrderedDict
    import pandas

    def nested_approx_(x, **kwargs):
        if isinstance(x, dict):
            return {k: nested_approx_(v, **kwargs) for k, v in x.items()}
        elif isinstance(x, OrderedDict):
            return OrderedDict(
                [(k, nested_approx_(v, **kwargs)) for k, v in x.items()])
        elif isinstance(x, list):
            return [nested_approx_(xx, **kwargs) for xx in x]
        elif isinstance(x, tuple):
            return tuple([nested_approx_(xx, **kwargs) for xx in x])
        elif isinstance(x, (pandas.DataFrame, ObjDict, PlyDict)):
            return x
        elif isinstance(x, (rapidjson.units.Quantity,
                            rapidjson.units.QuantityArray)):
            
            def units_equality(a, b):
                if a.units != b.units:
                    return False
                return pytest.approx(a.value, **kwargs) == b.value
            
            return patch_equality(x, units_equality)
        return pytest.approx(x, **kwargs)
    return nested_approx_


@pytest.fixture(scope="session")
def patch_equality():
    def patch_equality_w(obj, method):
        class EqualityWrapper:
            def __init__(self, x):
                self.x = x

            def __str__(self):
                return f"EqualityWrapper({self.x!s})"

            def __repr__(self):
                return f"EqualityWrapper({self.x!r})"
            
            def __eq__(self, other):
                if isinstance(other, EqualityWrapper):
                    y = other.x
                else:
                    y = other
                if not isinstance(y, self.x.__class__):
                    return False
                return method(self.x, y)
        return EqualityWrapper(obj)
    return patch_equality_w


# Fixtures for monitoring/managing resources
_dont_verify_count_fds = False
_dont_verify_count_comms = False
_dont_verify_count_threads = False
_fd_count = 0


@pytest.fixture(scope="session", autouse=True)
def init_mp():
    r"""Initialize multiprocessing."""
    from yggdrasil.multitasking import mp_ctx_spawn
    yield mp_ctx_spawn.RLock()


@pytest.fixture(scope="session", autouse=True)
def init_zmq():
    r"""Create a socket to remove initial fd count."""
    from yggdrasil.communication.ZMQComm import _global_context
    if _global_context:
        import zmq
        s = _global_context.socket(zmq.PUSH)
        s.close()


@pytest.fixture(scope="session")
def asan_installed():
    r"""Determine if ASAN is available."""
    from yggdrasil.drivers.CompiledModelDriver import (
        find_compilation_tool, get_compilation_tool)
    compiler = find_compilation_tool('compiler', 'c', allow_failure=True)
    if compiler:
        compiler = get_compilation_tool('compiler', compiler)
    return compiler and compiler.asan_library()


@pytest.fixture
def requires_asan(asan_installed):
    r"""Skip a test if it requires non-existent ASAN."""
    if not asan_installed:
        pytest.skip("ASAN library not available")


# @pytest.fixture(autouse=True)
# def ensure_gc():
#     gc.collect()
#     yield
#     gc.collect()


@pytest.fixture
def first_test():
    r"""Stand-in for first test."""
    return True


@pytest.fixture(scope="session")
def register_weakref():
    r"""Register a weak ref for use by another fixture."""
    def register_weakref_w(x):
        import weakref
        global _weakref_registry
        _weakref_registry.append(weakref.ref(x))
    return register_weakref_w


@pytest.fixture(scope="session")
def close_comm():
    r"""Close a communicator."""
    def close_comm_w(comm):
        comm.close()
        comm.disconnect()
        assert comm.is_closed
        del comm
    return close_comm_w


@pytest.fixture(scope="session")
def count_comms(communicator_types):
    r"""Count the number of communicators in existence."""
    def count_comms_w(classes=None):
        from yggdrasil.communication import import_comm
        if classes is None:
            classes = communicator_types
        return sum(import_comm(k).comm_count() for k in classes)
    return count_comms_w


@pytest.fixture(scope="session")
def count_fds():
    r"""Count the number of file descriptors."""
    def count_fds_w(dont_subtract_closed=False):
        import psutil
        from yggdrasil import platform
        proc = psutil.Process()
        if platform._is_win:  # pragma: windows
            out = proc.num_handles()
        else:
            conn = proc.connections()
            out = proc.num_fds()
            if not dont_subtract_closed:
                out -= len([x for x in conn if x.status == 'CLOSE'])
            # from yggdrasil.tools import get_fds
            # fd_list = get_fds(ignore_closed=(not dont_subtract_closed),
            #                   ignore_kqueue=True, verbose=True,
            #                   by_column=3)
            # out_alt = len(fd_list)
            # print(out_alt, out, len(conn))
            # assert out_alt == out
        return out
    return count_fds_w


@pytest.fixture(scope="session")
def list_fds():
    r"""Get a list of file descriptors."""
    from yggdrasil import tools

    def list_fds_w():
        return tools.get_fds()
    return list_fds_w


@pytest.fixture(scope="session")
def track_fds(list_fds):
    r"""Track the creation of fds."""
    from yggdrasil.tools import track_fds as track_fds_w
    return track_fds_w


@pytest.fixture(scope="session")
def log_resource_counts(count_comms, count_fds):
    r"""Log resource counts."""
    import threading

    def log_resource_counts_w(prefix=""):
        logger.debug(f"{prefix}comms={count_comms()}, fds={count_fds()}, "
                     f"threads={threading.active_count()}")
    return log_resource_counts_w


@pytest.fixture
def disable_verify_count_threads():
    global _dont_verify_count_threads
    _dont_verify_count_threads = True
    yield


@pytest.fixture
def optionally_disable_verify_count_fds():
    def optionally_disable_verify_count_fds_w():
        global _dont_verify_count_fds
        _dont_verify_count_fds = True
    return optionally_disable_verify_count_fds_w


@pytest.fixture
def disable_verify_count_fds(optionally_disable_verify_count_fds):
    optionally_disable_verify_count_fds()
    yield


@pytest.fixture
def disable_verify_count_comms():
    global _dont_verify_count_comms
    _dont_verify_count_comms = True
    yield


@pytest.fixture
def verify_count_threads(wait_on_function):
    r"""Assert that all threads created during a test are cleaned up."""
    import threading
    global _dont_verify_count_thrads
    _dont_verify_count_thrads = False
    nthread = threading.active_count()
    yield

    if not _dont_verify_count_thrads:
        def on_timeout():  # pragma: debug
            threads = '\n\t'.join([x.name for x in threading.enumerate()])
            raise AssertionError(f"{threading.active_count()} threads "
                                 f"running, but the test started with "
                                 f"{nthread}. Running threads:\n\t{threads}")
        # Subtract one as it will be the thread checking function
        wait_on_function(lambda: threading.active_count() <= (nthread + 1),
                         on_timeout=on_timeout)


@pytest.fixture
def verify_count_comms(wait_on_function, count_comms, communicator_types):
    r"""Verify that comms created during a test are cleaned up."""
    global _dont_verify_count_comms
    _dont_verify_count_comms = False
    ncomm = count_comms()
    yield

    if not _dont_verify_count_comms:
        def on_timeout():  # pragma: debug
            comms = '\n\t'.join([f"{x}:\t{count_comms([x])}"
                                 for x in communicator_types])
            raise AssertionError(f"{count_comms()} comms "
                                 f"in registry, but the test started with "
                                 f"{ncomm}. Available comms:\n\t{comms}")
        wait_on_function(lambda: count_comms() <= ncomm,
                         on_timeout=on_timeout)


@pytest.fixture(scope="session")
def reset_count_fds(count_fds):
    r"""Reset the global file descriptor count."""

    def wrapped(value=None):
        if value is None:
            value = count_fds()
        global _fd_count
        prev_count = _fd_count
        _fd_count = value
        return prev_count
    return wrapped
    
    
@pytest.fixture
def verify_count_fds(wait_on_function, first_test, count_fds,
                     init_zmq, init_mp):
    r"""Verify that file descriptors created during a test are cleaned up."""
    global _dont_verify_count_fds
    global _fd_count
    _dont_verify_count_fds = False
    _fd_count = count_fds()
    # from yggdrasil.tools import track_fds
    # with track_fds():
    yield
    gc.collect()
    if not (first_test or _dont_verify_count_fds or platform._is_win):
        def on_timeout():  # pragma: debug
            global _weakref_registry
            for x in _weakref_registry:
                if x():
                    import pdb
                    refs = gc.get_referrers(x())
                    print(f"{len(refs)} references remain")
                    pprint.pprint(refs)
                    print(f'FDS: {count_fds()}')
                    pdb.set_trace()
            # warnings.warn(f"{count_fds()} file descriptors are open, "
            #               f"but the test started with {_fd_count}.")
            raise AssertionError(f"{count_fds()} file descriptors are open, "
                                 f"but the test started with {_fd_count}.")
        wait_on_function(lambda: count_fds() <= _fd_count,
                         on_timeout=on_timeout)


@pytest.fixture
def cleanup_communicators(communicator_types):
    r"""Cleanup communicators."""
    yield
    from yggdrasil.communication import cleanup_comms
    for x in communicator_types:
        cleanup_comms(x)


# MPI utilities
_global_tag = 0
_mpi_error_exchange = None


def mpi_flavor():
    r"""Return the MPI flavor."""
    if shutil.which('mpicc'):
        result = subprocess.check_output("mpicc -v", shell=True).decode(
            "utf-8")
        if "MPICH" in result:
            return 'mpich'
        # elif "Open MPI" in result:
        return 'openmpi'
    return None


@pytest.fixture(scope="session")
def mpi_comm():
    r"""MPI communicator."""
    try:
        from mpi4py import MPI
        return MPI.COMM_WORLD
    except ImportError:
        return None


@pytest.fixture(scope="session")
def mpi_size(mpi_comm):
    r"""int: Size of MPI job."""
    if mpi_comm is None:
        return 1
    else:
        return mpi_comm.Get_size()


@pytest.fixture(scope="session")
def mpi_rank(mpi_comm):
    r"""int: MPI rank of the current process."""
    if mpi_comm is None:
        return 0
    else:
        return mpi_comm.Get_rank()


@pytest.fixture(scope="session")
def on_mpi(mpi_size):
    r"""bool: True if this is an MPI run."""
    return (mpi_size > 1)


def new_mpi_exchange():
    from yggdrasil.multitasking import MPIErrorExchange
    global _mpi_error_exchange
    global _global_tag
    if _mpi_error_exchange is None:
        _mpi_error_exchange = MPIErrorExchange(global_tag=_global_tag)
    else:
        _global_tag = _mpi_error_exchange.global_tag
        _mpi_error_exchange.reset(global_tag=_global_tag)
    return _mpi_error_exchange


@pytest.fixture(scope="session")
def adv_global_mpi_tag():
    def adv_global_mpi_tag_w(value=1):
        global _mpi_error_exchange
        assert _mpi_error_exchange is not None
        out = _mpi_error_exchange.global_tag
        _mpi_error_exchange.global_tag += value
        return out
    return adv_global_mpi_tag_w


@pytest.fixture(scope="session")
def sync_mpi_exchange():
    def sync_mpi_exchange_w(*args, **kwargs):
        global _mpi_error_exchange
        assert _mpi_error_exchange is not None
        return _mpi_error_exchange.sync(*args, **kwargs)
    return sync_mpi_exchange_w


# Method of raising errors when other process fails
# https://docs.pytest.org/en/latest/example/simple.html#
# making-test-result-information-available-in-fixtures
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()
    # set a report attribute for each phase of a call, which can
    # be "setup", "call", "teardown"
    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(autouse=True)
def sync_mpi_result(request, on_mpi):
    r"""Synchronize results between MPI ranks."""
    mpi_exchange = None
    if on_mpi:
        mpi_exchange = new_mpi_exchange()
        mpi_exchange.sync()
    yield
    if on_mpi:
        failure = (request.node.rep_setup.failed
                   or getattr(getattr(request.node, 'rep_call', None),
                              'failed', False))
        mpi_exchange.finalize(failure)


# Monkey patch pytest-cov plugin with MPI Barriers to prevent multiple
# MPI processes from attempting to modify the .coverage data file at
# the same time and limit the coverage output to the rank 0 process
@pytest.fixture(scope="session", autouse=True)
def finalize_mpi(request, on_mpi, mpi_comm, mpi_rank, mpi_size):
    """Slow down the exit on MPI processes to prevent collision in access
    to .coverage file."""
    if not on_mpi:
        return
    manager = request.config.pluginmanager
    plugin_class = manager.get_plugin('pytest_cov').CovPlugin
    plugin = None
    for x in manager.get_plugins():
        if isinstance(x, plugin_class):
            plugin = x
            break
    if not plugin:  # pragma: no cover
        return
    old_finish = getattr(plugin.cov_controller, 'finish')

    def new_finish():
        mpi_comm.Barrier()
        for _ in range(mpi_rank):
            mpi_comm.Barrier()
        old_finish()
        # These lines come after coverage collection
        for _ in range(mpi_rank, mpi_size):  # pragma: testing
            mpi_comm.Barrier()  # pragma: testing
        mpi_comm.Barrier()  # pragma: testing

    plugin.cov_controller.finish = new_finish
    if mpi_rank != 0:

        def new_is_worker(session):  # pragma: testing
            return True

        plugin._is_worker = new_is_worker


@pytest.fixture
def display_diff():

    def wrapped(a, b):
        import difflib
        a_str = pprint.pformat(a)
        b_str = pprint.pformat(b)
        diff = difflib.ndiff(a_str.splitlines(),
                             b_str.splitlines())
        print('\n'.join(diff))

    return wrapped


@pytest.fixture
def geom_dict():
    return {
        'vertices': np.array([[0, 0, 0, 0, 1, 1, 1, 1],
                              [0, 0, 1, 1, 0, 0, 1, 1],
                              [0, 1, 1, 0, 0, 1, 1, 0]], 'float32').T,
        'faces': np.array([[0, 0, 7, 0, 1, 2, 3],
                           [1, 2, 6, 4, 5, 6, 7],
                           [2, 3, 5, 5, 6, 7, 4]], 'int32').T}
