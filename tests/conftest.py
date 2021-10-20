import os
import gc
import re
import sys
import glob
import shutil
import pytest
import logging
import subprocess
import contextlib
from yggdrasil import platform, constants
from yggdrasil.tools import get_supported_lang, get_supported_comm
from yggdrasil.components import import_component
from yggdrasil.multitasking import _on_mpi
sys.path.append(os.path.join(os.path.dirname(__file__), 'helpers'))
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


_test_directory = os.path.dirname(__file__)
_test_registry = []
_weakref_registry = []
_markers = [
    ("long_running", "--long-running",
     "tests that take a long time to run", None),
    ("extra_example", "--extra-examples",
     "tests for superfluous examples", None),
    ("production_run", "--production-run", None)
]
_params = {
    "example_name": [],
    "language": sorted(constants.LANGUAGES['all']),
    "commtype": sorted(get_supported_comm()),
    "filetype": sorted(list(
        constants.COMPONENT_REGISTRY["file"]["subtypes"].keys())),
    "use_async": [False, True],
    "transform": None,
    "filter": None,
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


def extract_suites(args):
    suites = [x for x in args if x.startswith(('--suite', '--suites',
                                               '--test-suite'))]
    out = []
    for x in suites:
        if '=' in x:
            out.append(x.split('=', 1)[-1])
        else:
            idx = args.index(x) + 1
            while (idx < len(args)) and (not args[idx].startswith('-')):
                out.append(args[idx])
                idx += 1
    return out


# def pytest_load_initial_conftests(args):
def pytest_cmdline_preparse(args, dont_exit=False):
    r"""Adjust the pytest arguments before testing."""
    # TODO: count?
    # Check for run in separate process before adding CI args
    run_process = False
    prefix = []
    suites = extract_suites(args)
    # Disable output capture
    if '--nocapture' in args:
        args += ['-s', '-o', 'log_cli=true']
        args.remove('--nocapture')
    # MPI process should be started
    mpi_flag = [x for x in args if x.startswith('--run-with-mpi')]
    if ('mpi' in suites) and (not mpi_flag) and (not _on_mpi):
        mpi_flag = ['--run-with-mpi=2']
        args.append(mpi_flag[0])
    if mpi_flag:
        assert(len(mpi_flag) == 1)
        if '=' in mpi_flag[0]:
            nproc = mpi_flag[0].split('=', 1)[-1]
        else:
            idx = args.index(mpi_flag[0]) + 1
            nproc = args[idx]
            del args[idx]
        args.remove(mpi_flag[0])
        if int(nproc) > 1:
            run_process = True
            prefix = ['mpiexec', '-n', nproc]
            if '--with-mpi' not in args:
                args.append('--with-mpi')
            args += ['-p', 'no:flaky']
    # Write a script to call later
    write_script = [x for x in args if x.startswith('--write-script')]
    if write_script:
        assert(len(write_script) == 1)
        if '=' in write_script[0]:
            fname = write_script[0].split('=', 1)[-1]
        else:
            idx = args.index(write_script[0]) + 1
            fname = args[idx]
            del args[idx]
        if not os.path.isabs(fname):
            fname = os.path.abspath(fname)
        args.remove(write_script[0])
        write_pytest_script(fname,
                            prefix
                            + [sys.executable, '-m', 'pytest']
                            + args)
        if dont_exit:
            return 0
        sys.exit(0)
    # Check for separate tests
    separate_tests = [x for x in args if x.startswith('--separate-test')]
    for x in separate_tests:
        if '=' in x:
            x_args = x.split('=', 1)[-1].split()
        else:
            idx = args.index(x) + 1
            x_args = args[idx].split()
            del args[idx]
        args.remove(x)
        assert(any([xx.startswith('--write-script') for xx in x_args]))
        pytest_cmdline_preparse(x_args, dont_exit=True)
    # Run test in separate process
    if run_process:
        flag = subprocess.call(prefix
                               + [sys.executable, '-m', 'pytest']
                               + args)
        if dont_exit:
            return flag
        sys.exit(flag)
    # Continuous integration
    if '--ci' in args:
        import yggdrasil
        package_dir = os.path.abspath(os.path.dirname(yggdrasil.__file__))
        args += ['-v',
                 f'--cov={package_dir}',
                 '-c', 'setup.cfg',
                 '--cov-config=.coveragerc',
                 '--ignore=yggdrasil/rapidjson/',
                 f'--rootdir={package_dir}']
        if not any(x.startswith('--with-mpi') for x in args):
            args += ['--reruns=2', '--reruns-delay=1', '--timeout=900']
        # Additional checks
        if not os.path.isfile('setup.cfg'):
            raise RuntimeError("The CI tests must be run from the root "
                               "directory of the yggdrasil git repository.")
        top_dir = os.path.dirname(os.getcwd())
        src_cmd = ('python -c \"import versioneer; '
                   'print(versioneer.get_version())\"')
        dst_cmd = ('python -c \"import yggdrasil; '
                   'print(yggdrasil.__version__)\"')
        src_ver = subprocess.check_output(src_cmd, shell=True)
        dst_ver = subprocess.check_output(dst_cmd, shell=True, cwd=top_dir)
        if src_ver != dst_ver:  # pragma: debug
            raise RuntimeError(("Versions do not match:\n"
                                "\tSource version: %s\n"
                                "\tBuild  version: %s\n")
                               % (src_ver, dst_ver))
        subprocess.check_call(
            ["flake8", "yggdrasil", "--append-config", "setup.cfg"])
        if os.environ.get("YGG_CONDA", None):
            subprocess.check_call(["python", "create_coveragerc.py"])
        if not os.path.isfile(".coveragerc"):
            raise RuntimeError(".coveragerc file dosn't exist.")
        with open(".coveragerc", "r") as fd:
            print(fd.read())
        subprocess.check_call(["yggdrasil", "info", "--verbose"])
    # Add test suites paths
    suite_map = {x[0]: (x[2], x[3]) for x in _suites}
    suite_files = []
    for suite in suites:
        for f in suite_map[suite][0]:
            suite_files += glob.glob(os.path.join(_test_directory, f))
        args += suite_map[suite][1]
    if suite_files:
        existing_files = [x for x in args if
                          os.path.isdir(x)
                          or (os.path.isfile(x.split('::')[0])
                              and (x.split('::')[0].endswith(".py")))]
        if not existing_files:
            args += ['--end-yggdrasil-opts'] + sorted(suite_files)


def pytest_addoption(parser):
    languages = sorted(get_supported_lang())
    for x in _markers:
        parser.addoption(x[1], action="store_true", default=False,
                         help=f"run {x[2]} tests")
    for k, v in _params.items():
        if v is None:
            v = sorted(list(constants.COMPONENT_REGISTRY[k]["subtypes"].keys()))
        choices = v if v else None
        parser.addoption(f"--parametrize-{k.replace('_', '-')}",
                         help=f"Set '{k}' test parameter", nargs='*',
                         choices=choices)
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
    parser.addoption('--run-with-mpi', type=int, default=1,
                     help="Number of MPI processes to run tests on.")
    parser.addoption('--separate-tests', '--separate-test',
                     type=str, action="append",
                     help="Flags for an additional test that should be run")
    parser.addoption('--nocapture', action="store_true",
                     help="Don't capture output or log messages from tests.")
    parser.addoption('--end-yggdrasil-opts', action="store_true",
                     help="Internal use only")


def pytest_configure(config):
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
    for x in _markers:
        if config.getoption(x[1]):
            continue
        skip_x = pytest.mark.skip(reason=f"need {x[1]} to run")
        for item in items:
            if x[0] in item.keywords:
                item.add_marker(skip_x)
    # Handle suite & language markers
    selected_suites = config.getoption('--suite')
    enabled = config.getoption("--language")
    disabled = config.getoption("--skip-language")
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
        suites_disabled = [mark.kwargs.get('disabled', False)
                           for mark in item.iter_markers(name="suite")]
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
            if class_params:
                params = [x for x in params if x in class_params]
        elif class_params:
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
    if platform._is_win:
        lines = [' '.join(argv)]
    else:
        lines = ['#!/bin/bash',
                 ' '.join(argv)]
    with open(fname, 'w') as fd:
        fd.write('\n'.join(lines))
    os.chmod(fname, (stat.S_IRWXU
                     | stat.S_IRGRP | stat.S_IXGRP
                     | stat.S_IROTH | stat.S_IXOTH))
    print("Wrote test script to '%s':\n\t%s"
          % (fname, '\n\t'.join(lines)))


# Session level constants
@pytest.fixture(scope="session")
def project_dir():
    r"""Directory in which yggdrasil is installed."""
    import yggdrasil
    return os.path.abspath(os.path.dirname(yggdrasil.__file__))


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
def scripts():
    r"""Dictionary of test scripts for each language."""
    from yggdrasil import tools
    script_dir = os.path.join(os.path.dirname(__file__), 'scripts')
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
        ('osr', 'osr_model.xml')]
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
def yamls():
    r"""Dictionary of test YAMLs for each language."""
    yaml_dir = os.path.join(os.path.dirname(__file__), 'yamls')
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


# @pytest.fixture(scope="session")
# def field_name():
#     r"""Table field names."""
#     return [b'name', b'count', b'size']


# @pytest.fixture(scope="session")
# def field_units():
#     r"""Table field units."""
#     return [b'n/a', b'umol', b'cm']


# @pytest.fixture(scope="session")
# def comment():
#     r"""Comment character."""
#     return b'# '


# @pytest.fixture(scope="session")
# def newline():
#     r"""Newline character."""
#     return b'\n'


# Fixtures based on CLI options
@pytest.fixture(scope="session", autouse=True)
def config_env(pytestconfig):
    r"""Set environment variables based on CLI options."""
    production_run = pytestconfig.getoption("--production-run")
    default_comm = pytestconfig.getoption("--default-comm")
    debug = pytestconfig.getoption("--ygg-debug")
    loglevel = pytestconfig.getoption("--ygg-loglevel")
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
    assert(not check_running)
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
    def running_service_w(service_type, partial_commtype=None):
        from yggdrasil.services import (
            IntegrationServiceManager)
        check_service_manager_settings(service_type, partial_commtype)
        model_repo = "https://github.com/cropsinsilico/yggdrasil_models_test/models"
        log_level = logging.ERROR
        args = [sys.executable, "-m", "yggdrasil", "integration-service-manager",
                f"--service-type={service_type}"]
        if partial_commtype is not None:
            args.append(f"--commtype={partial_commtype}")
        args += ["start", f"--model-repository={model_repo}",
                 f"--log-level={log_level}"]
        process_kws = {}
        if with_coverage:
            script_path = os.path.expanduser(os.path.join('~', 'run_server.py'))
            process_kws['cwd'] = project_dir
            if platform._is_win:  # pragma: windows
                process_kws['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
            lines = [
                'from yggdrasil.services import IntegrationServiceManager',
                'srv = IntegrationServiceManager(']
            if service_type is not None:
                lines[-1] += f'service_type=\'{service_type}\''
                if partial_commtype is not None:
                    lines[-1] += ', '
            if partial_commtype is not None:
                lines[-1] += f'commtype=\'{partial_commtype}\''
            lines[-1] += ')'
            lines += ['assert(not srv.is_running)',
                      f'srv.start_server(with_coverage={with_coverage},',
                      f'                 log_level={log_level},'
                      f'                 model_repository=\'{model_repo}\')']
            with open(script_path, 'w') as fd:
                fd.write('\n'.join(lines))
            args = [sys.executable, script_path]
        verify_flask = (service_type == 'flask')
        if verify_flask:
            # Flask is the default, verify that it is selected
            service_type = None
        cli = IntegrationServiceManager(service_type=service_type,
                                        commtype=partial_commtype,
                                        for_request=True)
        if verify_flask:
            assert(cli.service_type == 'flask')
        assert(not cli.is_running)
        p = subprocess.Popen(args, **process_kws)
        try:
            cli.wait_for_server()
            yield cli
            cli.stop_server()
            assert(not cli.is_running)
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


@pytest.fixture(scope="session")
def check_required_languages(pytestconfig):
    r"""Check if a set of languages is enabled/disabled."""
    def check_required_languages_w(required_languages):
        enabled = pytestconfig.getoption("--language")
        disabled = pytestconfig.getoption("--skip-language")
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
                assert(msg_recv == recv_inst.eof_msg)
            return (not flag)
        wait_on_function(recv_element, timeout=timeout)
        if expected_result is not None:
            assert(msg_list == nested_approx(expected_result))
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
def unyts_equality(nested_approx):
    r"""Comparison operation for unyt quantities and arrays."""
    import unyt

    def unyts_equality_w(a, b):
        if not isinstance(b, unyt.array.unyt_array):
            return False
        if a.units != b.units:
            return False
        return a.to_ndarray() == nested_approx(b.to_ndarray())
    return unyts_equality_w


@pytest.fixture
def unyts_equality_patch(monkeypatch, unyts_equality):
    r"""Patch unyt array so that data and units considered."""
    import unyt
    with monkeypatch.context() as m:
        m.setattr(unyt.array.unyt_array, '__eq__', unyts_equality)
        yield
        

@pytest.fixture(scope="session")
def nested_approx(patch_equality, pandas_equality):
    r"""Nest pytest.approx for assertion."""
    from collections import OrderedDict
    import pandas
    import unyt

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
        elif isinstance(x, pandas.DataFrame):
            return x
        elif isinstance(x, (unyt.array.unyt_quantity, unyt.array.unyt_array)):
            # from yggdrasil.units import get_ureg
            # units = str(x.units)
            # y = pytest.approx(x, **kwargs)
            # dtype = x.to_ndarray().dtype
            # return x.__class__(y, units, dtype=dtype, registry=get_ureg())
            return x
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
                if not isinstance(other, self.x.__class__):
                    return False
                return method(self.x, other)
        return EqualityWrapper(obj)
    return patch_equality_w


# Fixtures for monitoring/managing resources
_dont_verify_count_fds = False
_dont_verify_count_comms = False
_dont_verify_count_threads = False


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
        assert(comm.is_closed)
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
    def count_fds_w():
        import psutil
        from yggdrasil import platform
        proc = psutil.Process()
        if platform._is_win:  # pragma: windows
            out = proc.num_handles()
        else:
            out = proc.num_fds()
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
def disable_verify_count_fds():
    global _dont_verify_count_fds
    _dont_verify_count_fds = True
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


@pytest.fixture
def verify_count_fds(wait_on_function, first_test, count_fds,
                     init_zmq, init_mp):
    r"""Verify that file descriptors created during a test are cleaned up."""
    global _dont_verify_count_fds
    _dont_verify_count_fds = False
    nfds = count_fds()
    yield
    gc.collect()
    if not (first_test or _dont_verify_count_fds):
        def on_timeout():  # pragma: debug
            global _weakref_registry
            for x in _weakref_registry:
                if x():
                    import pprint
                    import pdb
                    refs = gc.get_referrers(x())
                    print(f"{len(refs)} references remain")
                    pprint.pprint(refs)
                    print(f'FDS: {count_fds()}')
                    pdb.set_trace()
            raise AssertionError(f"{count_fds()} file descriptors are open, "
                                 f"but the test started with {nfds}.")
        wait_on_function(lambda: count_fds() <= nfds,
                         on_timeout=on_timeout)


@pytest.fixture
def cleanup_communicators(communicator_types):
    r"""Cleanup communicators."""
    yield
    from yggdrasil.communication import cleanup_comms
    for x in communicator_types:
        cleanup_comms(x)


# MPI utilities
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
