import os
import sys
import argparse
import uuid
import pprint
import shutil
import subprocess
import warnings
import difflib
import copy
from datetime import datetime
PYVER = ('%s.%s' % sys.version_info[:2])
PY2 = (sys.version_info[0] == 2)
if os.environ.get('PRE_CONDA_BIN', False):
    os.environ['PATH'] = (os.environ['PRE_CONDA_BIN']
                          + os.pathsep
                          + os.environ['PATH'])
_is_osx = (sys.platform == 'darwin')
_is_linux = ('linux' in sys.platform)
_is_win = (sys.platform in ['win32', 'cygwin'])
_is_unix = (_is_osx or _is_linux)
_on_gha = bool(os.environ.get('GITHUB_ACTIONS', False))
_on_travis = bool(os.environ.get('TRAVIS_OS_NAME', False))
_on_appveyor = bool(os.environ.get('APPVEYOR_BUILD_FOLDER', False))
_on_ci = (_on_gha or _on_travis or _on_appveyor)
_utils_dir = os.path.dirname(os.path.abspath(__file__))
_pkg_dir = os.path.dirname(_utils_dir)
CONDA_ENV = os.environ.get('CONDA_DEFAULT_ENV', None)
CONDA_PREFIX = os.environ.get('CONDA_PREFIX', None)
CONDA_INDEX = None
CONDA_ROOT = None
try:
    CONDA_CMD_WHICH = shutil.which('conda')
    YGG_CMD_WHICH = shutil.which('yggdrasil')
except AttributeError:
    if _is_win:
        CONDA_CMD_WHICH = None
        YGG_CMD_WHICH = None
    else:
        try:
            CONDA_CMD_WHICH = subprocess.check_output(
                ['which', 'conda']).strip().decode('utf-8')
        except subprocess.CalledProcessError:
            CONDA_CMD_WHICH = None
        try:
            YGG_CMD_WHICH = subprocess.check_output(
                ['which', 'yggdrasil']).strip().decode('utf-8')
        except subprocess.CalledProcessError:
            YGG_CMD_WHICH = None
if (not CONDA_PREFIX):
    if CONDA_CMD_WHICH:
        CONDA_PREFIX = os.path.dirname(os.path.dirname(CONDA_CMD_WHICH))
    elif _on_gha and os.environ.get('CONDA', None):
        CONDA_PREFIX = os.environ['CONDA']
    if CONDA_PREFIX and (not CONDA_ENV):
        CONDA_ENV = 'base'
if ((isinstance(CONDA_PREFIX, str)
     and os.path.dirname(CONDA_PREFIX).endswith('envs'))):
    CONDA_PREFIX = os.path.dirname(os.path.dirname(CONDA_PREFIX))
if CONDA_PREFIX:
    CONDA_INDEX = os.path.join(CONDA_PREFIX, "conda-bld")
    if not os.path.isdir(CONDA_INDEX):
        if _on_gha and _is_win and CONDA_PREFIX.endswith('Library'):
            CONDA_INDEX = os.path.join(os.path.dirname(CONDA_PREFIX),
                                       "conda-bld")
if CONDA_CMD_WHICH:
    if _is_win:
        CONDA_CMD = 'call conda'
        MAMBA_CMD = 'call mamba'
    else:
        CONDA_CMD = 'conda'
        MAMBA_CMD = 'mamba'
    CONDA_ROOT = os.path.dirname(os.path.dirname(CONDA_CMD_WHICH))
elif os.environ.get('CONDA', None):
    if _is_win:
        CONDA_CMD = 'call %s' % os.path.join(os.environ['CONDA'],
                                             'condabin', 'conda.bat')
        MAMBA_CMD = 'call %s' % os.path.join(os.environ['CONDA'],
                                             'condabin', 'mamba.bat')
    else:
        CONDA_CMD = os.path.join(os.environ['CONDA'], 'bin', 'conda')
        MAMBA_CMD = os.path.join(os.environ['CONDA'], 'bin', 'mamba')
    CONDA_ROOT = os.environ['CONDA']
else:
    CONDA_CMD = None
    MAMBA_CMD = None
PYTHON_CMD = sys.executable


class SetupParam(object):
    r"""Storage for setup parameters.

    Args:
        method (str): Method that should be used to build and install
            the package. Valid values include 'conda' and 'pip'.
        install_opts (dict, optional): Mapping from language/package
            to bool specifying whether or not the language/package
            should be installed. If not provided, get_install_opts is
            used to create it.
        target_os (str, optional): OS that should be targeted if
            different that the current one.
        fallback_to_conda (bool, optional): If True, conda will be
            used to install non-python dependencies and Python
            dependencies that cannot be installed via pip. Defaults to
            False.
        use_mamba (bool, optional): If True, use mamba in place of
            conda. Defaults to False.
        for_development (bool, optional): If True, requirements will
            be treated as if yggdrasil will be installed for
            development.
        only_python (bool, optional): If True, only Python package
            will be considered. Defaults to False.
        windows_package_manager (str, optional): Package manager that
            should be used for non-Python packages when outside a
            conda environment. Defaults to vcpkg.
        conda_env (str, optional): Name of the conda environment that
            packages should be installed in. Defaults to None and is
            ignored.
        always_yes (bool, optional): If True, conda commands are
            called with -y flag so that user interaction is not
            required. Defaults to False.
        verbose (bool, optional): If True, setup steps are run with
            verbosity turned up. Defaults to False.

    """

    def __init__(self, method=None, install_opts=None, target_os=None,
                 fallback_to_conda=None, use_mamba=False,
                 for_development=False, only_python=False,
                 windows_package_manager='vcpkg',
                 conda_env=None, always_yes=False, verbose=False):
        self.method = method
        self.install_opts = get_install_opts(install_opts)
        self.target_os = target_os
        self.fallback_to_conda = fallback_to_conda
        self.use_mamba = use_mamba
        self.for_development = for_development
        self.only_python = only_python
        self.windows_package_manager = windows_package_manager
        self.conda_env = conda_env
        self.always_yes = always_yes
        self.verbose = verbose
        self.conda_flags = ''
        self.pip_flags = ''
        # Modified inputs vars:
        #   use_mamba, method, fallback_to_conda, install_opts,
        #   target_os
        if self.target_os is None:
            self.target_os = self.install_opts['os']
        else:
            assert self.target_os in ['linux', 'osx', 'win', 'any']
            self.install_opts['os'] = self.target_os
        if self.method is None:
            if self.use_mamba:
                self.method = 'conda'
            elif CONDA_ENV:
                self.method = 'conda'
            else:
                self.method = 'pip'
        elif self.method.startswith('mamba'):
            self.use_mamba = True
            self.method = self.method.replace('mamba', 'conda')
        self.python_cmd = PYTHON_CMD
        if self.conda_env:
            self.python_cmd = locate_conda_exe(conda_env, 'python',
                                               use_mamba=self.use_mamba)
            self.conda_flags += f' --name {self.conda_env}'
        if self.always_yes:
            self.conda_flags += ' -y'
            # self.pip_flags += ' -y'
        if self.verbose:
            self.conda_flags += ' -vvv'
            self.pip_flags += ' --verbose'
        # else:
        #     self.conda_flags += '-q'
        if self.method.endswith('-dev'):
            self.method_base = self.method.split('-dev')[0]
            self.for_development = True
        else:
            self.method_base = self.method
        self.conda_exe_config = CONDA_CMD
        if self.use_mamba:
            self.conda_exe = MAMBA_CMD
            # self.conda_build = f"{CONDA_CMD} mambabuild"
            # self.build_pkgs = ["boa"]
        else:
            self.conda_exe = CONDA_CMD
            # self.conda_build = f"{CONDA_CMD} build"
            # self.build_pkgs = ["conda-build", "conda-verify"]
        # self.conda_env = CONDA_ENV
        # self.conda_idx = CONDA_INDEX
        if self.fallback_to_conda is None:
            self.fallback_to_conda = ((self.method_base == 'conda')
                                      or (_is_win and _on_appveyor)
                                      or self.install_opts['lpy'])
        self.kwargs = {}
        for k in ['verbose', 'install_opts', 'conda_env', 'always_yes',
                  'fallback_to_conda', 'use_mamba']:
            self.kwargs[k] = getattr(self, k)
        if self.for_development:
            self.install_opts['dev'] = True
        # Methods that can be used to install deps
        self.deps_methods = ['skip', 'python', 'cran']
        self.deps_methods += ['pip', 'pip_skip']
        if self.fallback_to_conda:
            self.deps_methods += ['conda', 'conda_skip']
        else:
            if self.install_opts['os'] == 'linux':
                self.deps_methods.append('apt')
            elif self.install_opts['os'] == 'osx':
                self.deps_methods.append('brew')
            elif self.install_opts['os'] == 'win':
                self.deps_methods.append(self.windows_package_manager)

    @classmethod
    def from_args(cls, args, install_opts):
        args_to_copy = [
            'target_os', 'for_development',
            'windows_package_manager', 'conda_env',
            'verbose', 'always_yes', 'only_python', 'use_mamba']
        cls.extract_install_opts_from_args(args, install_opts)
        kwargs = {}
        for k in args_to_copy:
            if hasattr(args, k):
                kwargs[k] = getattr(args, k)
        return cls(args.method, install_opts=install_opts, **kwargs)

    @staticmethod
    def extract_install_opts_from_args(args, install_opts):
        new_opts = {}
        for k, v in install_opts.items():
            if k == 'no_sudo':
                new_opts[k] = bool(getattr(args, k, False))
            elif v and getattr(args, f'dont_install_{k}', False):
                new_opts[k] = False
            elif (not v) and getattr(args, f'install_{k}', False):
                new_opts[k] = True
        install_opts.update(new_opts)
    
    @staticmethod
    def add_parser_args(parser, skip=None, no_install=False,
                        install_opts=None):
        r"""Add arguments to a parser for installation options.

        Args:
            parser (argparse.ArgumentParser): Parser to add arguments to.
            skip (list, optional): Arguments that should not be added.
                Defaults to an empty list.
            install_opts (dict, optional): Existing installation options
                that should be used to set the flags. Create using
                get_install_opts if not provided.

        """
        if skip is None:
            skip = []
        if no_install:
            skip += ['conda_env', 'always_yes', 'verbose']

        def add_argument(*args, **kwargs):
            for x in args:
                x = x.strip('-')
                if x in skip or x.replace('-', '_') in skip:
                    return
            parser.add_argument(*args, **kwargs)

        add_argument(
            '--target-os', choices=['win', 'osx', 'linux'],
            help=("Operating system that environment should target if "
                  "different from the current OS."))
        add_argument(
            '--for-development', action='store_true',
            help=("Install dependencies used during development and "
                  "that would be missed when installing in development mode. "
                  "Implies --include-dev-deps"))
        add_argument(
            '--windows-package-manager', default='vcpkg',
            help="Package manager that should be used on Windows.",
            choices=['vcpkg', 'choco'])
        add_argument(
            '--conda-env', '-n', default=None,
            help="Conda environment that packages should be installed in.")
        add_argument(
            '--verbose', action='store_true',
            help="Turn up verbosity of output.")
        add_argument(
            '--always-yes', action='store_true',
            help="Pass -y to conda commands to avoid user interaction.")
        add_argument(
            '--only-python', '--python-only', action='store_true',
            help="Only install python dependencies.")
        add_argument('--use-mamba', action='store_true',
                     help="Use mamba in place of conda")
        # method?, fallback_to_conda,
        add_install_opts_args(parser, install_opts=install_opts)


def get_summary_commands(use_mamba=False):
    r"""Get commands to use to summarize the state of the environment.

    Args:
        use_mamba (bool, optional): If True, use mamba in place of conda.

    Returns:
        list: Commands.

    """
    setup_param = SetupParam(use_mamba=use_mamba)
    out = [f"{setup_param.python_cmd} --version",
           f"{setup_param.python_cmd} -m pip list"]
    if CONDA_ENV:
        out += [f"echo 'CONDA_PREFIX={CONDA_PREFIX}'",
                f"{setup_param.conda_exe} info",
                f"{setup_param.conda_exe} list",
                f"{setup_param.conda_exe_config} config --show-sources"]
    return out


def call_conda_command(args, use_mamba=False, **kwargs):
    r"""Function for calling conda commands as the conda script is not
    available on subprocesses for windows unless invoked via the shell.

    Args:
        args (list): Command arguments.
        **kwargs: Additional keyword arguments are passed to subprocess.check_output.
        use_mamba (bool, optional): If True, use mamba in place of conda.

    Returns:
        str: The output from the command.

    """
    if _is_win:
        args = ' '.join(args)
        kwargs['shell'] = True  # Conda commands must be run on the shell
    return subprocess.check_output(args, **kwargs).decode("utf-8")


def call_script(lines, force_bash=False, verbose=False):
    r"""Write lines to a script and call it.

    Args:
        lines (list): Lines that should be written to the script.
        force_bash (bool, optional): If True, bash will be used, even
            on windows. Defaults to False.
        verbose (bool, optional): If True, each line will be printed before
            it is executed.

    """
    # if _on_gha:
    verbose = True
    if not lines:
        return
    # Split lines that should be allowed to fail
    line_sets = []
    idx = 0
    for i, line in enumerate(lines):
        if line.endswith('# [ALLOW FAIL]'):
            line_sets.append(lines[idx:i])
            line_sets.append([lines[i]])
            idx = i + 1
    line_sets.append(lines[idx:])
    for lines in line_sets:
        allow_failure = lines[0].endswith('# [ALLOW FAIL]')
        if allow_failure:
            lines = [lines[0].split('#')[0].strip()]
        if verbose:
            for i in range(len(lines) - 1, 0, -1):
                line_str = lines[i].replace('"', '\\"')
                lines.insert(i, f'echo "CALLING: {line_str}"')
        if _is_win and (not force_bash):  # pragma: windows
            script_ext = '.bat'
            error_check = 'if %errorlevel% neq 0 exit /b %errorlevel%'
            for i in range(len(lines), 0, -1):
                lines.insert(i, error_check)
        else:
            script_ext = '.sh'
            if lines[0] != '#!/bin/bash':
                lines.insert(0, '#!/bin/bash')
            error_check = 'set -e'
            if error_check not in lines:
                lines.insert(1, error_check)
        fname = 'ci_script_%s%s' % (str(uuid.uuid4()), script_ext)
        try:
            pprint.pprint(lines)
            with open(fname, 'w') as fd:
                fd.write('\n'.join(lines))
                
            call_kws = {}
            if _is_win:  # pragma: windows
                call_cmd = [os.environ['COMSPEC'], '/c', 'call', fname]
            else:
                call_cmd = ['./%s' % fname]
                os.chmod(fname, 0o755)
            subprocess.check_call(call_cmd, **call_kws)
        except subprocess.CalledProcessError:
            if not allow_failure:
                raise
        finally:
            if os.path.isfile(fname):
                os.remove(fname)


def conda_env_exists(name, use_mamba=False):
    r"""Determine if a conda environment already exists.

    Args:
        name (str): Name of the environment to check.
        use_mamba (bool, optional): If true, use mamba.

    Returns:
        bool: True the the environment exits, False otherwise.

    """
    if use_mamba:
        cmd = MAMBA_CMD
    else:
        cmd = CONDA_CMD
    args = [cmd, 'info', '--envs']
    out = call_conda_command(args, use_mamba=use_mamba)
    envs = []
    for x in out.splitlines():
        if x.startswith('#') or (not x):
            continue
        envs.append(x.split()[0])
    return (name in envs)


def locate_conda_bin(conda_env, use_mamba=False):
    r"""Determine the full path to the bin directory in a specific
    conda environment.

    Args:
        conda_env (str): Name of conda environment that executable should be
            returned for.
        use_mamba (bool, optional): If True, use mamba in place of conda.

    Returns:
        str: Full path to the directory.

    """
    assert CONDA_ROOT
    conda_prefix = os.path.join(CONDA_ROOT, 'envs')
    if sys.platform in ['win32', 'cygwin']:
        out = os.path.join(conda_prefix, conda_env, 'Scripts')
    else:
        out = os.path.join(conda_prefix, conda_env, 'bin')
    return out


def locate_conda_exe(conda_env, name, use_mamba=False):
    r"""Determine the full path to an executable in a specific conda environment.

    Args:
        conda_env (str): Name of conda environment that executable should be
            returned for.
        name (str): Name of the executable to locate.
        use_mamba (bool, optional): If True, use mamba in place of conda.

    Returns:
        str: Full path to the executable.

    """
    if sys.platform in ['win32', 'cygwin'] and not name.endswith('.exe'):
        name += '.exe'
    out = os.path.join(
        locate_conda_bin(conda_env, use_mamba=use_mamba), name)
    if sys.platform in ['win32', 'cygwin'] and name.startswith('python'):
        out = os.path.dirname(out)
    try:
        assert os.path.isfile(out)
    except AssertionError:
        out = os.path.expanduser(os.path.join('~', '.conda', 'envs', name))
        if not os.path.isfile(out):
            raise
    return out


def get_install_opts(old=None, empty=False):
    r"""Get optional language/package installation options from CI
    environment variables.

    Args:
        old (dict, optional): If provided, the returned mapping will include
            the values from this dictionary, but will also be updated with any
            that are missing.

    Returns:
        dict: Mapping between languages/packages and whether or not they
            should be installed.

    """
    if empty:
        new = {
            'c': False,
            'lpy': False,
            'r': False,
            'fortran': False,
            'zmq': False,
            'sbml': False,
            'astropy': False,
            'rmq': False,
            'trimesh': False,
            'pygments': False,
            'omp': False,
            'docs': False,
            'no_sudo': False,
            'mpi': False,
            'dev': False,
            'testing': False,
            'empty': True,
        }
    elif _on_ci:
        new = {
            'c': (os.environ.get('INSTALLC', '0') == '1'),
            'lpy': (os.environ.get('INSTALLLPY', '0') == '1'),
            'r': (os.environ.get('INSTALLR', '0') == '1'),
            'fortran': (os.environ.get('INSTALLFORTRAN', '0') == '1'),
            'zmq': (os.environ.get('INSTALLZMQ', '0') == '1'),
            'sbml': (os.environ.get('INSTALLSBML', '0') == '1'),
            'astropy': (os.environ.get('INSTALLAPY', '0') == '1'),
            'rmq': (os.environ.get('INSTALLRMQ', '0') == '1'),
            'trimesh': (os.environ.get('INSTALLTRIMESH', '0') == '1'),
            'pygments': (os.environ.get('INSTALLPYGMENTS', '0') == '1'),
            'omp': (os.environ.get('INSTALLOMP', '0') == '1'),
            'docs': (os.environ.get('BUILDDOCS', '0') == '1'),
            'no_sudo': False,
            'mpi': (os.environ.get('INSTALLMPI', '0') == '1'),
            'dev': False,
            'testing': True,
        }
        if not _is_win:
            new['c'] = True  # c compiler usually installed by default
    else:
        new = {
            'c': True,
            'lpy': False,
            'r': True,
            'fortran': True,
            'zmq': True,
            'sbml': False,
            'astropy': False,
            'rmq': False,
            'trimesh': True,
            'pygments': True,
            'omp': False,
            'docs': False,
            'no_sudo': False,
            'mpi': False,
            'dev': False,
            'testing': True,
        }
    if empty:
        new['os'] = 'any'
    elif _is_win:
        new['os'] = 'win'
    elif _is_osx:
        new['os'] = 'osx'
    elif _is_linux:
        new['os'] = 'linux'
    if old is None:
        out = {}
    else:
        out = old.copy()
    for k, v in new.items():
        out.setdefault(k, v)
    if not out.get('empty', False):
        if not out['c']:
            out.update(fortran=False, zmq=False)
        if out['docs']:
            out['r'] = True  # Allow roxygen
    return out


def add_install_opts_args(parser, install_opts=None):
    r"""Add arguments to a parser for installation options.

    Args:
        parser (argparse.ArgumentParser): Parser to add arguments to.
        install_opts (dict, optional): Existing installation options
            that should be used to set the flags. Create using
            get_install_opts if not provided.

    """
    if install_opts is None:
        install_opts = get_install_opts()
    for k, v in install_opts.items():
        if k in ['os']:
            continue
        elif k == 'no_sudo':
            parser.add_argument(
                '--no-sudo', action='store_true',
                help="Don't use sudo during installation.")
            continue
        if v:
            parser.add_argument(
                '--dont-install-%s' % k, action='store_true',
                help=("Don't install %s" % k))
        else:
            parser.add_argument(
                '--install-%s' % k, action='store_true',
                help=("Install %s" % k))


def create_env(method, python, name=None, packages=None, init=_on_ci,
               use_mamba=False, verbose=False):
    r"""Setup a test environment on a CI resource.

    Args:
        method (str): Method that should be used to create an environment.
            Supported values currently include 'conda', 'mamba', and
            'virtualenv'.
        python (str): Version of Python that should be tested.
        name (str, optional): Name that should be used for the environment.
            Defaults to None and will be craeted based on the method and
            Python version.
        packages (list, optional): Packages that should be installed in the new
            environment. Defaults to None and is ignored.
        init (bool, optional): If True, the environment management program is
            first configured as if it is on CI so that some interactive
            aspects will be disabled. Default is set based on the presence of
            CI environment variables (it currently checks for Github Actions,
            Travis CI, and Appveyor).
        use_mamba (bool, optional): If True, use mamba in place of conda.
        verbose (bool, optional): If True, each line will be printed before
            it is executed.

    Raises:
        ValueError: If method is not 'conda', 'mamba', or 'pip'.

    """
    cmds = [f"echo Creating test environment using {method}..."]
    major, minor = [int(x) for x in python.split('.')][:2]
    if name is None:
        name = method + python.replace('.', '')
    setup_param = SetupParam(method, verbose=verbose, use_mamba=use_mamba)
    if packages is None:
        packages = []
    if 'pyyaml' not in packages:  # Required to load requirements
        packages.append('pyyaml')
    # if 'requests' not in packages:
    #     # Not strictly required, but useful for determine the versions of
    #     # dependencies required by packages during testing
    #     packages.append('requests')
    if setup_param.method == 'conda':
        conda_exe_config = setup_param.conda_exe_config
        conda_exe = setup_param.conda_exe
        if conda_env_exists(name, use_mamba=setup_param.use_mamba):
            print(f"Conda env with name '{name}' already exists.")
            return
        if init:
            cmds += [
                # Configure conda
                f"{conda_exe_config} config --set always_yes yes --set changeps1 no",
                f"{conda_exe_config} config --set channel_priority strict",
                f"{conda_exe_config} config --prepend channels conda-forge",
                f"{conda_exe_config} update -q {setup_param.method}",
                # f"{conda_exe_config} config --set allow_conda_downgrades true",
                # f"{conda_exe} install -n root conda=4.9",
            ]
        cmds += [
            (f"{conda_exe} create -q -n {name} python={python} "
             + ' '.join(packages))
        ]
    elif setup_param.method == 'virtualenv':
        python_cmd = setup_param.python_cmd
        if (sys.version_info[0] != major) or (sys.version_info[1] != minor):
            if _is_osx:
                try:
                    call_script(['python%d --version' % major])
                except BaseException:
                    cmds.append('brew install python%d' % major)
                try:
                    python_cmd = shutil.which('python%d' % major)
                except AttributeError:
                    python_cmd = 'python%d' % major
            else:  # pragma: debug
                raise RuntimeError(("The version of Python (%d.%d) does not match the "
                                    "desired version (%s) and virtualenv cannot create "
                                    "an environment with a different version of Python.")
                                   % (sys.version_info[0], sys.version_info[1], python))
        cmds += [
            f"{python_cmd} -m pip install --upgrade pip virtualenv",
            f"virtualenv -p {python_cmd} {name}"
        ]
        if packages:
            cmds.append(f"{python_cmd} -m pip install " + ' '.join(packages))
    else:  # pragma: debug
        raise ValueError(f"Unsupport environment management method:"
                         f" '{setup_param.method}'")
    call_script(cmds, verbose=verbose)


def build_pkg(method, python=None, return_commands=False,
              verbose=False, use_mamba=False):
    r"""Build the package on a CI resource.

    Args:
        method (str): Method that should be used to build the package.
            Valid values include 'conda', 'mamba', and 'pip'.
        python (str, optional): Version of Python that package should be
            built for. Defaults to None if not provided and the current
            version of Python will be used.
        return_commands (bool, optional): If True, the commands necessary to
            build the package are returned instead of running them. Defaults
            to False.
        verbose (bool, optional): If True, setup steps are run with verbosity
            turned up. Defaults to False.
        use_mamba (bool, optional): If True, use mamba in place of conda.

    """
    if python is None:
        python = PYVER
    setup_param = SetupParam(method, verbose=verbose, use_mamba=use_mamba)
    cmds = []
    # Upgrade pip and setuptools and wheel to get clean install
    upgrade_pkgs = ['wheel', 'setuptools']
    if not _is_win:
        upgrade_pkgs.insert(0, 'pip')
    if setup_param.method == 'conda':
        conda_env = CONDA_ENV
        conda_idx = CONDA_INDEX
        if setup_param.use_mamba:
            conda_build = f"{CONDA_CMD} mambabuild"
            build_pkgs = ["boa"]
        else:
            conda_build = f"{CONDA_CMD} build"
            build_pkgs = ["conda-build", "conda-verify"]
        if verbose:
            build_flags = ''
        else:
            build_flags = '-q'
        # Must always build in base to avoid errors (and don't change the
        # version of Python used in the environment)
        # https://github.com/conda/conda/issues/9124
        # https://github.com/conda/conda/issues/7758#issuecomment-660328841
        assert conda_env == 'base'
        assert conda_idx
        if _on_gha:
            cmds += [
                f"{setup_param.conda_exe_config} config --prepend channels"
                f" conda-forge",
                f"{setup_param.conda_exe} update -q {setup_param.method}",
            ]
        if _is_win and _on_gha:
            # The tests issue a command that is too long for the
            # windows command prompt which is used to build the conda
            # package on Github Actions
            build_flags += ' --no-test'
        cmds += [
            f"{setup_param.conda_exe} clean --all"]  # Might invalidate cache
        if not (_is_win and _on_gha):
            cmds += [f"{setup_param.conda_exe} update --all"]
        cmds += [
            f"{setup_param.conda_exe} install -q -n base " + ' '.join(build_pkgs),
            f"{conda_build} recipe --python {python} {build_flags}"
        ]
        cmds.append(f"{setup_param.conda_exe} index {conda_idx}")
    elif setup_param.method == 'pip':
        if verbose:
            build_flags = ''
        else:
            build_flags = '--quiet'
        # Install from source dist
        cmds += [f"{setup_param.python_cmd} -m pip install --upgrade "
                 + ' '.join(upgrade_pkgs)]
        cmds += [f"{setup_param.python_cmd} setup.py {build_flags} sdist"]
    else:  # pragma: debug
        raise ValueError(f"Method must be 'conda', 'mamba', or 'pip', not"
                         f" '{setup_param.method}'")
    if return_commands:
        return cmds
    summary_cmds = get_summary_commands(use_mamba=setup_param.use_mamba)
    cmds = summary_cmds + cmds + summary_cmds
    if setup_param.use_mamba and not shutil.which('mamba'):
        cmds.insert(0, f"{CONDA_CMD} install mamba -c conda-forge")
    call_script(cmds, verbose=verbose)
    if setup_param.method == 'conda':  # and not setup_param.use_mamba:
        print(f"CONDA_IDX = {conda_idx}")
        assert (conda_idx and os.path.isdir(conda_idx))


def create_env_yaml(filename='environment.yml', name='env', channels=None,
                    install_opts=None, target_os=None, python_version=None,
                    **kwargs):
    r"""Create an environment.yml file.

    Args:
        filename (str, optional): Path where the generate file should be
            saved. Defaults to 'environment.yml'.
        name (str, optional): Name of environment that should be
            created by the file. Defaults to 'env'.
        channels (list, optional): Conda channels that should be used in the
            environment file. Defaults to []. 'conda-forge' will be added
            if it is not already present.
        install_opts (dict, optional): Mapping from language/package to bool
            specifying whether or not the language/package should be installed.
            If not provided, get_install_opts is used to create it.
        target_os (str, optional): Operating system that the generated file
            should target. Defaults to the current OS.
        python_version (str, optional): Python version that environment
            should target. Defaults to the current Python version if not
            provided.
        **kwargs: Additional keyword arguments are passed to itemize_deps.

    """
    import yaml
    import platform
    from install_from_requirements import prune
    if channels is None:
        channels = []
    if 'conda-forge' not in channels:
        channels.append('conda-forge')
    if python_version is None:
        python_version = ".".join(platform.python_version_tuple()[:2])
    environment = {'python_version': python_version}
    if target_os is not None:
        if target_os == 'linux':
            environment["os_name"] = 'Linux'
        elif target_os == 'osx':
            environment["os_name"] = 'Darwin'
        elif target_os == 'win':
            environment["os_name"] = 'Windows'
    install_opts = get_install_opts(install_opts)
    pkgs = itemize_deps('conda', install_opts=install_opts, **kwargs)
    deps = prune(pkgs['requirements'] + pkgs['requirements_conda'],
                 install_opts=install_opts, excl_method='pip',
                 additional_packages=pkgs['conda'],
                 skip_packages=pkgs['skip'],
                 return_list=True, environment=environment,
                 verbose=True)
    deps.insert(0, 'python=' + python_version)
    data = {'name': name,
            'channels': channels,
            'dependencies': deps}
    with open(filename, 'w') as fd:
        yaml.dump(data, fd, Dumper=yaml.SafeDumper)
    return filename


def itemize_deps(method, for_development=False,
                 windows_package_manager='vcpkg', install_opts=None,
                 fallback_to_conda=None, use_mamba=False,
                 skipped_mpi=False):
    r"""Get lists of dependencies.
    
    Args:
        method (str): Method that should be used to install the package dependencies.
            Valid values include 'conda', 'mamba', and 'pip'.
        for_development (bool, optional): If True, dependencies are installed that would
            be missed when installing in development mode. Defaults to False.
        windows_package_manager (str, optional): Name of the package
            manager that should be used on windows. Defaults to 'vcpkg'.
        install_opts (dict, optional): Mapping from language/package to bool
            specifying whether or not the language/package should be installed.
            If not provided, get_install_opts is used to create it.
        fallback_to_conda (bool, optional): If True, conda will be used to install
            non-python dependencies and Python dependencies that cannot be installed
            via pip. Defaults to False.
        use_mamba (bool, optional): If True, use mamba in place of conda.
        skipped_mpi (list, optional): Existing list that skipped mpi
            packages should be added to. Defaults to False and is
            ignored.

    Returns:
        dict: Dependencies grouped by the package manager that should be
            used.

    """
    from manage_requirements import select_requirements
    param = SetupParam(
        method,
        install_opts=install_opts,
        fallback_to_conda=fallback_to_conda,
        windows_package_manager=windows_package_manager,
        use_mamba=use_mamba,
        for_development=for_development)
    out = select_requirements(param, for_setup=True)
    if True:  # pragma: debug
        import difflib
        pkgs_old = itemize_deps_old(
            param.method,
            for_development=param.for_development,
            windows_package_manager=param.windows_package_manager,
            install_opts=param.install_opts,
            fallback_to_conda=param.fallback_to_conda,
            use_mamba=param.use_mamba,
            no_files=True)
        s_old = pprint.pformat(pkgs_old)
        s_new = pprint.pformat(out)
        print(f"Old version\n{s_old}")
        print(f"New version\n{s_new}")
        print('\n'.join(difflib.ndiff(s_old.splitlines(),
                                      s_new.splitlines())))
    return out

    
def itemize_deps_old(
        method, for_development=False,
        windows_package_manager='vcpkg', install_opts=None,
        fallback_to_conda=None, use_mamba=False,
        skipped_mpi=False, no_files=False):
    r"""Get lists of dependencies.
    
    Args:
        method (str): Method that should be used to install the package dependencies.
            Valid values include 'conda', 'mamba', and 'pip'.
        for_development (bool, optional): If True, dependencies are installed that would
            be missed when installing in development mode. Defaults to False.
        windows_package_manager (str, optional): Name of the package
            manager that should be used on windows. Defaults to 'vcpkg'.
        install_opts (dict, optional): Mapping from language/package to bool
            specifying whether or not the language/package should be installed.
            If not provided, get_install_opts is used to create it.
        fallback_to_conda (bool, optional): If True, conda will be used to install
            non-python dependencies and Python dependencies that cannot be installed
            via pip. Defaults to False.
        use_mamba (bool, optional): If True, use mamba in place of conda.
        skipped_mpi (list, optional): Existing list that skipped mpi
            packages should be added to. Defaults to False and is
            ignored.
        no_files (bool, optional): If True, all requirements in files
            will be moved into the returned dictionary. Defaults to
            False.

    Returns:
        dict: Dependencies grouped by the package manager that should be
            used.

    """
    from install_from_requirements import (
        get_pip_dependency_version, DependencyNotFound)
    out = {'conda': [], 'pip': [], 'os': [], 'skip': [],
           'apt': [], 'brew': [], 'choco': [], 'vcpkg': [],
           'requirements': ['requirements_optional.txt'],
           'requirements_conda': [], 'requirements_pip': []}
    if no_files:
        out['python'] = []
    setup_param = SetupParam(method,
                             for_development=for_development,
                             install_opts=install_opts,
                             fallback_to_conda=fallback_to_conda,
                             windows_package_manager=windows_package_manager,
                             use_mamba=use_mamba)
    install_opts = setup_param.install_opts
    fallback_to_conda = setup_param.fallback_to_conda
    if no_files:
        out['default'] = out['python']
    elif setup_param.method == 'conda':
        out['default'] = out['conda']
    elif setup_param.method == 'pip':
        out['default'] = out['pip']
    else:  # pragma: debug
        raise ValueError(f"Method must be 'conda', 'mamba' or 'pip',"
                         f" not '{setup_param.method}'")
    # In the case of a development environment install requirements that
    # would be missed when installing in development mode
    if setup_param.for_development:
        if setup_param.method == 'conda':
            out['requirements'] += ['requirements.txt',
                                    'requirements_condaonly.txt']
        elif setup_param.method == 'pip':
            # requirements.txt not needed because dev install will
            # pick up and install those deps
            out['requirements'] += ['requirements_piponly.txt']
        out['default'].append('ipython')
    if setup_param.install_opts['testing']:
        out['requirements'].append('requirements_testing.txt')
    if setup_param.install_opts['dev']:
        out['requirements'].append('requirements_dev.txt')
    if (setup_param.method == 'pip') and fallback_to_conda:
        out['requirements_conda'] += ['requirements_condaonly.txt']
    elif setup_param.method == 'conda':
        out['requirements_pip'] += ['requirements.txt',
                                    'requirements_piponly.txt']
    # Required for non-strict channel priority
    # https://github.com/conda-forge/conda-forge.github.io/pull/670
    # https://conda.io/projects/conda/en/latest/user-guide/concepts/ ...
    #    packages.html?highlight=openblas#installing-numpy-with-blas-variants
    # if fallback_to_conda:
    #     conda_pkgs.append("\"blas=*=openblas\"")
    # Installing via pip causes import error on Windows and
    # a conflict when installing LPy
    out['conda'] += ['scipy', os.environ.get('NUMPY', 'numpy')]
    for k in ['matplotlib', 'jsonschema']:
        if os.environ.get(k.upper(), k) != k:
            out['default'].append(os.environ[k.upper()])
    if install_opts['os'] == 'linux':
        out['os'] += ["strace", "valgrind"]
    elif install_opts['os'] == 'osx':
        # There was a bug with the valgrind installation on GHA
        # out['os'] += ["valgrind"]
        pass
    if install_opts['omp'] and (not fallback_to_conda):
        if install_opts['os'] == 'linux':
            out['os'].append('libomp-dev')
        elif install_opts['os'] == 'osx':
            out['os'] += ['libomp', 'llvm']
        elif install_opts['os'] == 'win':
            pass
    if install_opts['mpi']:
        if not fallback_to_conda:
            if install_opts['os'] == 'linux':
                out['os'] += ['openmpi-bin', 'libopenmpi-dev']
            elif install_opts['os'] == 'osx':
                out['os'].append('openmpi')
            elif install_opts['os'] == 'win':
                pass
        elif setup_param.method == 'conda':
            if install_opts['os'] == 'win':
                # Force mpi4py to be installed last on Windows to
                # avoid conflicts
                out['skip'] += ['mpi4py', 'msmpi']
            elif install_opts['os'] == 'osx' and setup_param.use_mamba:
                out['os'].append('openmpi')
                out['skip'] += ['mpi4py', 'openmpi', 'mpich']
    if install_opts['fortran'] and (not fallback_to_conda):
        # Fortran is not installed via conda on linux/macos
        if install_opts['os'] == 'linux':
            out['os'].append("gfortran")
        elif install_opts['os'] == 'osx':
            out['os'].append("gcc")
            out['os'].append("gfortran")
        elif install_opts['os'] == 'win' and (not fallback_to_conda):
            out['choco'] += ["mingw"]
            # out['vcpkg'].append("vcpkg-gfortran")
    if install_opts['r'] and (not fallback_to_conda):
        # TODO: Test split installation where r-base is installed from
        # conda and the R dependencies are installed from CRAN?
        if install_opts['os'] == 'linux':
            if not shutil.which('R'):
                out['os'] += ["r-base", "r-base-dev"]
            out['os'] += ["libudunits2-dev"]
        elif install_opts['os'] == 'osx':
            if not shutil.which('R'):
                out['os'] += ["r"]
            out['os'] += ["udunits"]
        elif install_opts['os'] == 'win':
            if not shutil.which('R'):
                out['choco'] += [
                    "r.project --params \"\'/AddToPath\'\"",
                    "rtools"]
        else:
            raise NotImplementedError("Could not determine "
                                      "R installation method.")
    if install_opts['zmq'] and (not fallback_to_conda):
        if install_opts['os'] == 'linux':
            out['os'] += ["libczmq-dev", "libzmq3-dev"]
        elif install_opts['os'] == 'osx':
            out['os'] += ["czmq", "zmq"]
        elif install_opts['os'] == 'win':
            out['vcpkg'] += ["czmq", "zeromq"]
        else:
            raise NotImplementedError("Could not determine "
                                      "ZeroMQ installation method.")
    if install_opts['docs']:
        out['requirements'].append('requirements_docs.txt')
        if not fallback_to_conda:
            out['os'].append("doxygen")
            if install_opts['os'] == 'linux':
                out['os'] += ["pandoc"]
            elif install_opts['os'] == 'osx':
                out['os'] += ["pandoc-citeproc", "Caskroom/cask/mactex"]
            else:
                NotImplementedError("Could not determine "
                                    "pandoc installation method.")
    if install_opts['sbml'] and fallback_to_conda:
        # Until the sbml package is updated to allow numpy != 1.19.3,
        # sbml will need to be installed separately without deps in order
        # to work in a conda env
        numpy_ver = 'numpy==1.19.3'
        try:
            new_numpy_ver = get_pip_dependency_version(
                'libroadrunner', 'numpy')
            if new_numpy_ver != numpy_ver:
                warnings.warn(
                    "libroadrunner has updated it's numpy requirement. "
                    "Assuming the new requirement is not strict (%s), "
                    "this code can be removed and libroadrunner can be "
                    "installed normally (numpy should be installed with "
                    "conda if a conda environment is being used to avoid "
                    "inconsistencies)." % new_numpy_ver)
            numpy_ver = new_numpy_ver
        except (ImportError, ModuleNotFoundError, DependencyNotFound):
            pass
        out['conda'].insert(0, numpy_ver.replace('==', '>='))
        out['skip'].append('libroadrunner')
    if install_opts['astropy'] and fallback_to_conda and _on_travis:
        out['conda'].insert(0, 'astropy>=4.1')
    if ((install_opts['fortran'] and fallback_to_conda
         and (_on_travis or (_on_gha and (install_opts['os'] == 'osx'))))):
        out['conda'].append('fortran-compiler')
    if not fallback_to_conda:
        out['default'] += out['conda']
    # Determine package manager based on OS
    if install_opts['os'] == 'linux':
        out['apt'] += out['os']
    elif install_opts['os'] == 'osx':
        out['brew'] += out['os']
    elif install_opts['os'] == 'win':
        if setup_param.windows_package_manager == 'choco':
            out['choco'] += out['os']
        elif setup_param.windows_package_manager == 'vcpkg':
            out['vcpkg'] += out['os']
        else:
            raise NotImplementedError(
                f"Invalid package manager:"
                f" '{setup_param.windows_package_manager}'")
    out.pop('os')
    if no_files:
        from install_from_requirements import prune
        import platform
        python_version = ".".join(platform.python_version_tuple()[:2])
        environment = {'python_version': python_version}
        if setup_param.target_os is not None:
            if setup_param.target_os == 'linux':
                environment["os_name"] = 'Linux'
            elif setup_param.target_os == 'osx':
                environment["os_name"] = 'Darwin'
            elif setup_param.target_os == 'win':
                environment["os_name"] = 'Windows'
        out['python'] += prune(out['requirements'],
                               excl_method=['pip', 'conda'],
                               environment=environment,
                               install_opts=setup_param.install_opts,
                               return_list=True)
        del out['default']
        if fallback_to_conda:
            out['conda'] += prune(
                out['requirements_conda'] + out['requirements'],
                incl_method='conda', environment=environment,
                install_opts=setup_param.install_opts,
                return_list=True)
        out['pip'] += prune(
            out['requirements_pip'] + out['requirements'],
            incl_method='pip', environment=environment,
            install_opts=setup_param.install_opts,
            return_list=True)
        for k in ['requirements', 'requirements_conda',
                  'requirements_pip']:
            out.pop(k, None)
        for k, v in list(out.items()):
            if not v:
                del out[k]
            else:
                out[k] = sorted(v)
    return out


def preinstall_deps(method, return_commands=False, verbose=False,
                    install_opts=None, conda_env=None, always_yes=False,
                    fallback_to_conda=None, use_mamba=False,
                    no_packages=False):
    r"""Pre-install packages with test specific versions.

    Args:
        method (str): Method that should be used to install the package dependencies.
            Valid values include 'conda', 'mamba', and 'pip'.
        return_commands (bool, optional): If True, the commands necessary to
            install the dependencies are returned instead of running them. Defaults
            to False.
        verbose (bool, optional): If True, setup steps are run with verbosity
            turned up. Defaults to False.
        install_opts (dict, optional): Mapping from language/package to bool
            specifying whether or not the language/package should be installed.
            If not provided, get_install_opts is used to create it.
        conda_env (str, optional): Name of the conda/mamba environment that
            packages should be installed in. Defaults to None and is ignored.
        always_yes (bool, optional): If True, conda/mamba commands are called
            with -y flag so that user interaction is not required. Defaults
            to False.
        fallback_to_conda (bool, optional): If True, conda/mamba will be used
            to install non-python dependencies and Python dependencies that
            cannot be installed via pip. Defaults to False.
        use_mamba (bool, optional): If True, use mamba in place of conda.
        no_package (bool, optional): If True, no packages are uninstalled or
            installed. Defaults to False.

    """
    setup_param = SetupParam(method,
                             verbose=verbose,
                             install_opts=install_opts,
                             conda_env=conda_env,
                             always_yes=always_yes,
                             fallback_to_conda=fallback_to_conda,
                             use_mamba=use_mamba)
    conda_prefix = '$CONDA_PREFIX'
    conda_root = CONDA_ROOT
    cmds = []
    # Uninstall default numpy and matplotlib to allow installation
    # of specific versions
    pre_conda = []
    pre_default = []
    if not no_packages:
        # Installing via pip causes import error on Windows and
        #  a conflict when installing LPy
        pre_conda += ['scipy', 'numpy']
        pre_default += ['matplotlib', 'jsonschema']
        if setup_param.method != 'conda':
            cmds += [f"{setup_param.python_cmd} -m pip uninstall -y "
                     + ' '.join(pre_conda + pre_default)]
        pre_conda = [os.environ[k.upper()] for k in pre_conda
                     if os.environ.get(k.upper(), k) != k]
        pre_default = [os.environ[k.upper()] for k in pre_default
                       if os.environ.get(k.upper(), k) != k]
    # Refresh channel
    # https://github.com/conda/conda/issues/8051
    if setup_param.fallback_to_conda and _on_gha:
        cmds += [
            f"{setup_param.conda_exe_config} config --set channel_priority strict",
            # These commands will not be valid for mamba
            # f"{setup_param.conda_exe} install -n root conda=4.9",
            # f"{setup_param.conda_exe_config} config --set "
            # f" allow_conda_downgrades true",
            f"{setup_param.conda_exe_config} config --remove channels conda-forge",
            f"{setup_param.conda_exe_config} config --prepend channels conda-forge",
        ]
    if setup_param.fallback_to_conda and not no_packages:
        cmds.append(f"{setup_param.conda_exe} update --all")
    if _on_gha and _is_unix and setup_param.fallback_to_conda:
        if conda_env:
            conda_prefix = os.path.join(conda_root, 'envs', conda_env)
        # Do both to ensure that the path is set for the installation
        # and in following steps
        cmds += [
            f"export LD_LIBRARY_PATH={conda_prefix}/lib:$LD_LIBRARY_PATH",
            "echo -n \"LD_LIBRARY_PATH=\" >> $GITHUB_ENV",
            f"echo {conda_prefix}/lib:$LD_LIBRARY_PATH >> $GITHUB_ENV"
        ]
        # TODO: Remove this once manage_requirements is complete
        if not no_packages:
            if setup_param.method == 'conda':
                pre_conda += pre_default
            elif setup_param.method == 'pip' and pre_default:
                cmds += [f"{setup_param.python_cmd} -m pip install"
                         f" {' '.join(pre_default)}"]
            if setup_param.fallback_to_conda and pre_conda:
                cmds += [f"{setup_param.conda_exe} install"
                         f" {setup_param.conda_flags} {' '.join(pre_conda)}"]
        cmds += get_summary_commands(use_mamba=setup_param.use_mamba)
    if return_commands:
        return cmds
    call_script(cmds, verbose=verbose)


def install_deps(method, return_commands=False, do_preinstall=False,
                 skipped_mpi=False, dry_run=False, **kwargs):
    r"""Install the package dependencies.
    
    Args:
        method (str): Method that should be used to install the
            package dependencies. Valid values include 'conda',
            'mamba', and 'pip'.
        return_commands (bool, optional): If True, the commands
            necessary to install the dependencies are returned instead
            of running them. Defaults to False.
        do_preinstall (bool, optional): If True, steps are taken to
            prepare for installation. Defaults to False.
        skipped_mpi (list, optional): Existing list that skipped mpi
            packages should be added to. Defaults to False and is
            ignored.
        dry_run (bool, optional): If True, the dependencies are
            displayed but not actually installed. Defaults to False.
        **kwargs: Additional keyword arguments are passed to
            SetupParam.

    """
    from manage_requirements import install_requirements
    setup_param = SetupParam(method, **kwargs)
    cmds = []
    # Prepare env
    if do_preinstall:
        cmds += preinstall_deps(setup_param.method,
                                return_commands=True,
                                **setup_param.kwargs)
    cmds += install_requirements(setup_param, dry_run=dry_run,
                                 return_commands=True)
    if not dry_run:
        call_script(cmds, verbose=setup_param.verbose)
    return cmds


def install_deps_old(
        method, return_commands=False, verbose=False,
        install_opts=None, conda_env=None, always_yes=False,
        only_python=False, fallback_to_conda=None,
        use_mamba=False, do_preinstall=False,
        skipped_mpi=False, dry_run=False, **kwargs):
    r"""Install the package dependencies.
    
    Args:
        method (str): Method that should be used to install the package dependencies.
            Valid values include 'conda', 'mamba', and 'pip'.
        return_commands (bool, optional): If True, the commands necessary to
            install the dependencies are returned instead of running them. Defaults
            to False.
        verbose (bool, optional): If True, setup steps are run with verbosity
            turned up. Defaults to False.
        install_opts (dict, optional): Mapping from language/package to bool
            specifying whether or not the language/package should be installed.
            If not provided, get_install_opts is used to create it.
        conda_env (str, optional): Name of the conda/mamba environment that
            packages should be installed in. Defaults to None and is ignored.
        always_yes (bool, optional): If True, conda/mamba commands are called
            with -y flag so that user interaction is not required. Defaults
            to False.
        only_python (bool, optional): If True, only Python packages will be installed.
            Defaults to False.
        fallback_to_conda (bool, optional): If True, conda/mamba will be used
            to install non-python dependencies and Python dependencies that
            cannot be installed via pip. Defaults to False.
        use_mamba (bool, optional): If True, use mamba in place of conda.
        do_preinstall (bool, optional): If True, steps are taken to prepare
            for installation. Defaults to False.
        skipped_mpi (list, optional): Existing list that skipped mpi
            packages should be added to. Defaults to False and is
            ignored.
        dry_run (bool, optional): If True, the dependencies are displayed
            but not actually installed. Defaults to False.
        **kwargs: Additional keyword arguments are passed to itemize_deps.

    """
    from install_from_requirements import install_from_requirements
    setup_param = SetupParam(method,
                             verbose=verbose,
                             install_opts=install_opts,
                             conda_env=conda_env,
                             always_yes=always_yes,
                             fallback_to_conda=fallback_to_conda,
                             only_python=only_python,
                             use_mamba=use_mamba)
    install_opts = setup_param.install_opts
    fallback_to_conda = setup_param.fallback_to_conda
    cmds = []
    # Get list of packages
    pkgs = itemize_deps(setup_param.method,
                        fallback_to_conda=fallback_to_conda,
                        install_opts=install_opts,
                        use_mamba=setup_param.use_mamba, **kwargs)
    if dry_run:
        return
    # Prepare env
    if do_preinstall:
        cmds += preinstall_deps(setup_param.method, return_commands=True,
                                **setup_param.kwargs)
    # if install_opts['r'] and (not fallback_to_conda) and (not only_python):
    #     # TODO: Test split installation where r-base is installed from
    #     # conda and the R dependencies are installed from CRAN?
    #     if _is_linux:
    #         if install_opts['no_sudo']:
    #             cmds += [
    #                 ("add-apt-repository 'deb https://cloud"
    #                  ".r-project.org/bin/linux/ubuntu xenial-cran35/'"),
    #                 ("apt-key adv --keyserver keyserver.ubuntu.com "
    #                  "--recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9")]
    #         else:
    #             cmds += [
    #                 ("sudo add-apt-repository 'deb https://cloud"
    #                  ".r-project.org/bin/linux/ubuntu xenial-cran35/'"),
    #                 ("sudo apt-key adv --keyserver keyserver.ubuntu.com "
    #                  "--recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9")]
    # Install dependencies using package manager(s)
    if not setup_param.only_python:
        if pkgs['apt']:
            if install_opts['no_sudo']:
                cmds += ["apt -y update"]
                cmds += ["apt-get -y install %s" % ' '.join(pkgs['apt'])]
            else:
                cmds += ["sudo apt update"]
                cmds += ["sudo apt-get install %s" % ' '.join(pkgs['apt'])]
        if pkgs['brew']:
            if 'gcc' in pkgs['brew']:
                cmds += ["brew reinstall gcc"]
                pkgs['brew'].remove('gcc')
            # if 'valgrind' in pkgs['brew']:
            #     cmds += ["brew tap LouisBrunner/valgrind",
            #              "brew install --HEAD LouisBrunner/valgrind/valgrind"]
            pkgs_from_src = []
            if _on_travis:
                for k in ['zmq', 'czmq', 'zeromq']:
                    if k in pkgs['brew']:
                        pkgs_from_src.append(k)
                        pkgs['brew'].remove(k)
            if pkgs_from_src:
                cmds += ["brew install --build-from-source %s" % ' '.join(pkgs_from_src)]
            if pkgs['brew']:
                cmds += ["brew install %s" % ' '.join(pkgs['brew'])]
        if pkgs['choco']:
            # cmds += ["choco install %s" % ' '.join(pkgs['choco'])]
            for x in pkgs['choco']:
                cmds.append("choco install %s --force" % x)
        if pkgs['vcpkg']:
            cmds += ["%s install %s --triplet x64-windows"
                     % ('vcpkg.exe', ' '.join(pkgs['vcpkg']))]
    # Install via requirements
    req_kwargs = dict(conda_env=conda_env,
                      python_cmd=setup_param.python_cmd,
                      install_opts=install_opts, append_cmds=cmds,
                      skip_packages=pkgs['skip'], verbose=verbose,
                      verbose_prune=True, use_mamba=setup_param.use_mamba,
                      skipped_mpi=skipped_mpi)
    install_from_requirements(setup_param.method, pkgs['requirements'],
                              additional_packages=pkgs['default'],
                              **req_kwargs)
    # Remove so that they are not installed twice
    pkgs.pop(setup_param.method, None)
    if fallback_to_conda:
        # TODO: Install requirements_optional here to catch optional
        #   conda packages
        install_from_requirements('conda', pkgs['requirements_conda'],
                                  additional_packages=pkgs.get('conda', []),
                                  unique_to_method=True, **req_kwargs)
    install_from_requirements('pip', pkgs['requirements_pip'],
                              additional_packages=pkgs.get('pip', []),
                              unique_to_method=True, **req_kwargs)
    if 'libroadrunner' in pkgs['skip']:
        pip_flags = '--no-dependencies'
        if verbose:
            pip_flags += ' --verbose'
        cmds.append(f'{setup_param.python_cmd} -m pip install'
                    f' {pip_flags} \"libroadrunner<2.0.7\"')
    if install_opts['lpy']:
        if fallback_to_conda:
            cmds += [f"{setup_param.conda_exe} install"
                     f" {setup_param.conda_flags}"
                     f" openalea.lpy boost=1.66.0 -c openalea"]
        else:  # pragma: debug
            raise RuntimeError("Could not detect conda environment. "
                               "Cannot proceed with a conda deployment "
                               "(required for LPy).")
    # if _is_win and install_opts['mpi'] and fallback_to_conda:
    #     # This is required as the install script for mpi4py aborts without
    #     # an error message when called inside a Python subprocess. This seems
    #     # to occur during cleanup for the installation process as the mpi4py
    #     # installation is functional. Possibly triggered by the activation script?
    #     cmds += [f"{setup_param.conda_exe} install"
    #              f" {setup_param.conda_flags}"
    #              f" mpi4py # [ALLOW FAIL]"]
    summary_cmds = get_summary_commands(use_mamba=setup_param.use_mamba)
    cmds += summary_cmds
    if return_commands:
        return cmds
    cmds = summary_cmds + cmds
    call_script(cmds, verbose=verbose)


def install_pkg(method, python=None, without_build=False,
                without_deps=False, verbose=False,
                windows_package_manager='vcpkg', install_opts=None, conda_env=None,
                always_yes=False, only_python=False, fallback_to_conda=None,
                use_mamba=False, install_deps_before=False):
    r"""Build and install the package and its dependencies on a CI
    resource.

    Args:
        method (str): Method that should be used to build and install
            the package. Valid values include 'conda' and 'pip'.
        python (str, optional): Version of Python that package should be
            built for. Defaults to None if not provided and the current
            version of Python will be used. This will be ignored if
            without_build is True.
        without_build (bool, optional): If True, the package will not be
            built prior to install. Defaults to False.
        without_deps (bool, optional): If True the package dependencies will
            not be installed prior to installing the package. Defaults to
            False.
        verbose (bool, optional): If True, setup steps are run with verbosity
            turned up. Defaults to False.
        windows_package_manager (str, optional): Name of the package
            manager that should be used on windows. Defaults to 'vcpkg'.
        install_opts (dict, optional): Mapping from language/package to bool
            specifying whether or not the language/package should be installed.
            If not provided, get_install_opts is used to create it.
        conda_env (str, optional): Name of the conda environment that packages
            should be installed in. Defaults to None and is ignored.
        always_yes (bool, optional): If True, conda commands are called with -y flag
            so that user interaction is not required. Defaults to False.
        only_python (bool, optional): If True, only Python packages will be installed.
            Defaults to False.
        fallback_to_conda (bool, optional): If True, conda will be used to install
            non-python dependencies and Python dependencies that cannot be installed
            via pip. Defaults to False.
        use_mamba (bool, optional): If True, use mamba in place of conda.
            Defaults to False.
        install_deps_before (bool, optional): If True, install deps before the
            package is installed. Set to true in the case of pip or dev
            environments to handle non-Python dependencies before yggdrasil
            is installed. Defaults to False.

    Raises:
        ValueError: If method is not 'conda' or 'pip'.

    """
    setup_param = SetupParam(method,
                             verbose=verbose,
                             install_opts=install_opts,
                             conda_env=conda_env,
                             always_yes=always_yes,
                             fallback_to_conda=fallback_to_conda,
                             only_python=only_python,
                             windows_package_manager=windows_package_manager,
                             use_mamba=use_mamba)
    method = setup_param.method
    install_opts = setup_param.install_opts
    fallback_to_conda = setup_param.fallback_to_conda
    use_mamba = setup_param.use_mamba
    if setup_param.method != 'conda' and not setup_param.only_python:
        # For pip and dev environments, non-Python deps should be installed
        #   before yggdrasil
        install_deps_before = True
    cmds = []
    if setup_param.for_development:
        without_build = True
    summary_cmds = get_summary_commands(use_mamba=setup_param.use_mamba)
    if not without_build:
        cmds += build_pkg(setup_param.method_base, python=python,
                          return_commands=True, verbose=verbose,
                          use_mamba=setup_param.use_mamba)
        cmds += summary_cmds
    cmds_deps = []
    cmds += preinstall_deps(setup_param.method_base, return_commands=True,
                            verbose=verbose, install_opts=install_opts,
                            conda_env=conda_env, always_yes=always_yes,
                            fallback_to_conda=fallback_to_conda,
                            use_mamba=setup_param.use_mamba)
    skipped_mpi = []
    if not without_deps:
        skipped_mpi = []
        cmds_deps += install_deps(
            setup_param.method_base,
            return_commands=True, verbose=verbose,
            for_development=setup_param.for_development,
            install_opts=install_opts,
            windows_package_manager=setup_param.windows_package_manager,
            conda_env=conda_env, always_yes=always_yes,
            only_python=setup_param.only_python,
            fallback_to_conda=fallback_to_conda,
            use_mamba=setup_param.use_mamba,
            skipped_mpi=skipped_mpi)
    if install_deps_before:
        cmds += cmds_deps
    extras = [x for x in ['mpi', 'rmq'] if install_opts[x]]
    # Install yggdrasil
    if method == 'conda':
        conda_exe_config = CONDA_CMD
        if setup_param.use_mamba:
            conda_exe = MAMBA_CMD
            conda_idx = CONDA_INDEX  # 'local'
        else:
            conda_exe = CONDA_CMD
            conda_idx = CONDA_INDEX
        assert (conda_idx and os.path.isdir(conda_idx))
        # Install from conda build
        # Assumes that the target environment is active
        install_flags = setup_param.conda_flags
        # if setup_param.use_mamba:
        #     index_channel = 'local'
        # else:
        if not setup_param.use_mamba:
            install_flags += ' --update-deps'
        if _is_win:
            index_channel = conda_idx
        else:
            index_channel = f"file:/{conda_idx}"
        extras += [x for x in ['c', 'fortran', 'r'] if install_opts[x]]
        ygg_pkgs = ['yggdrasil']
        ygg_pkgs += [f'yggdrasil.{x}' for x in extras]
        cmds += [
            f"{conda_exe_config} config --prepend channels {index_channel}",
            # Related issues if this stops working again
            # https://github.com/conda/conda/issues/466#issuecomment-378050252
            f"{conda_exe} install {install_flags} -c"
            f" {index_channel} {' '.join(ygg_pkgs)}"
            # Required for non-strict channel priority
            # https://github.com/conda-forge/conda-forge.github.io/pull/670
            # https://conda.io/projects/conda/en/latest/user-guide/concepts/ ...
            # packages.html?highlight=openblas#installing-numpy-with-blas-variants
            # f"{conda_exe} install {install_flags} --update-deps -c
            #   {index_channel} yggdrasil \"blas=*=openblas\""
        ]
        if skipped_mpi:
            assert ' install ' in cmds[-1]
            cmds[-1] = (f"{cmds[-1]} {' '.join(skipped_mpi)}"
                        f"# [ALLOW FAIL]")
        cmds += [f"{conda_exe} list"]
    elif method == 'pip':
        if _is_win:  # pragma: windows
            cmds += [
                "for %%a in (\"dist\\*.tar.gz\") do set YGGSDIST=%%a",
                "echo %YGGSDIST%"
            ]
            sdist = "%YGGSDIST%"
        else:
            sdist = "dist/*.tar.gz"
        if extras:
            sdist += f"[{','.join(extras)}]"
        cmds += [
            f"{setup_param.python_cmd} -m pip install"
            f" {setup_param.pip_flags} {sdist}",
            f"{setup_param.python_cmd} create_coveragerc.py"
        ]
    elif method.endswith('-dev'):
        # Call setup.py in separate process from the package directory
        # cmds += [f"{setup_param.python_cmd} setup.py develop"]
        pass
    else:  # pragma: debug
        raise ValueError(f"Invalid method: '{setup_param.method}'")
    if YGG_CMD_WHICH:
        cmds = []
    if not install_deps_before:
        cmds += cmds_deps
    # if skipped_mpi and not _is_win:
    #     # Do not install MPI with mamba as it seems to fallback
    #     # on the empty mpich (external_*) on macOS currently. See:
    #     #   https://github.com/mamba-org/mamba/issues/924
    #     cmds.append(
    #         f"{CONDA_CMD} install {setup_param.conda_flags}"
    #         f" {' '.join(skipped_mpi)}")
    # Print summary of what was installed
    if cmds:
        cmds = summary_cmds + cmds + summary_cmds
        call_script(cmds, verbose=verbose)
    if not YGG_CMD_WHICH and method.endswith('-dev'):
        src = '.'
        if extras:
            src += f"[{','.join(extras)}]"
        print(call_conda_command([setup_param.python_cmd,
                                  '-m', 'pip', 'install',
                                  '--editable', src],
                                 cwd=_pkg_dir,
                                 use_mamba=setup_param.use_mamba))
    # Follow up if on Unix as R installation may require sudo
    if install_opts['r'] and _is_unix:
        R_cmd = ["ygginstall", "r"]
        if not install_opts['no_sudo']:
            R_cmd.append("--sudoR")
        subprocess.check_call(R_cmd)
    if method == 'conda':
        env = copy.copy(os.environ)
        if (not install_opts['no_sudo']) and install_opts['r']:
            env['YGG_USE_SUDO_FOR_R'] = '1'
        src_dir = os.path.join(os.getcwd(),
                               os.path.dirname(os.path.dirname(__file__)))
        subprocess.check_call([setup_param.python_cmd,
                               "create_coveragerc.py"],
                              cwd=src_dir, env=env)


def verify_pkg(install_opts=None):
    r"""Verify that the package was installed correctly.

    Args:
        install_opts (dict, optional): Mapping from language/package to bool
            specifying whether or not the language/package should be installed.
            If not provided, get_install_opts is used to create it.

    """
    call_script(get_summary_commands())
    install_opts = get_install_opts(install_opts)
    if _is_win and (not install_opts['zmq']):
        install_opts['c'] = False
        install_opts['fortran'] = False
    elif (not install_opts['fortran']) and shutil.which('gfortran'):
        install_opts['fortran'] = True
    # if (not install_opts['r']) and shutil.which('Rscript'):
    #     if not (_on_gha and _is_linux):
    #         # The installation on GHA-ubuntu machines requires sudo
    #         # and so installation will not be complete unless it is
    #         # enabled explicitly. This does not seem to be True on
    #         # GHA-macos builds and R is not installed by default on
    #         # Travis/Appveyor.
    #         install_opts['r'] = True
    if (not install_opts['c']) and shutil.which('gcc') and (not _is_win):
        install_opts['c'] = True
    src_dir = os.path.join(os.getcwd(),
                           os.path.dirname(os.path.dirname(__file__)))
    src_version = subprocess.check_output(
        ["python", "-c",
         "'import versioneer; print(versioneer.get_version())'"],
        cwd=src_dir)
    bld_version = subprocess.check_output(
        ["python", "-c",
         "'import yggdrasil; print(yggdrasil.__version__)'"],
        cwd=os.path.dirname(src_dir))
    if src_version != bld_version:
        raise RuntimeError("Installed version does not match the version of "
                           "this source code.\n"
                           "\tSource version: %s\n\tBuild  version: %s"
                           % (src_version, bld_version))
    if install_opts['r']:
        assert shutil.which("R")
        assert shutil.which("Rscript")
    subprocess.check_call(["flake8", "yggdrasil"], cwd=src_dir)
    if not os.path.isfile(".coveragerc"):
        raise RuntimeError(".coveragerc file dosn't exist.")
    with open(".coveragerc", "r") as fd:
        print(fd.read())
    subprocess.check_call(["ygginfo", "--verbose"], cwd=src_dir)
    if install_opts['c']:
        subprocess.check_call(["yggccflags"], cwd=src_dir)
        subprocess.check_call(["yggldflags"], cwd=src_dir)
    # Verify that languages are installed
    sys.stdout.flush()
    from yggdrasil.tools import is_lang_installed, is_comm_installed
    errors = []
    for name in ['c', 'r', 'fortran', 'sbml', 'lpy']:
        flag = install_opts[name]
        if flag and (not is_lang_installed(name)):
            errors.append("Language '%s' should be installed, but is not."
                          % name)
        elif (not flag) and is_lang_installed(name):
            if name in ['r']:
                # Allow R to be installed even if the settings is not as
                # packages may be installed from CRAN, unless there is an
                # error which can occur when a new release of a dependency
                # comes out but there are not yet binaries available
                continue
            errors.append("Language '%s' should NOT be installed, but is."
                          % name)
    for name in ['zmq', 'rmq']:
        flag = install_opts[name]
        if name == 'rmq':
            language = 'python'  # rmq dosn't work for C
        else:
            language = None
        if flag and (not is_comm_installed(name, language=language)):
            errors.append("Comm '%s' should be installed, but is not." % name)
        elif (not flag) and is_comm_installed(name, language=language):
            errors.append("Comm '%s' should NOT be installed, but is." % name)
    if install_opts['mpi'] and not shutil.which('mpiexec'):
        paths = ["/usr/local", os.environ.get('CONDA', False),
                 os.environ.get('CONDA_PREFIX', False),
                 '/Library/Frameworks/Python.framework/Versions/Current']
        cmds = []
        for x in paths:
            if not x:
                continue
            cmds.append(f"ls {os.path.join(x, 'bin')}")
            for k in ['mpiexec', 'mpirun', 'mpicc']:
                cmds.append(f"find {x} -xdev -name '*{k}*'")
        cmds += ['conda-tree whoneeds -t mpich',
                 'conda-tree whoneeds -t mpi4py',
                 'conda-tree whoneeds -t libgfortran',
                 'conda-tree whoneeds -t clang',
                 'conda-tree depends -t yggdrasil']
        call_script(cmds)
        errors.append("mpiexec could not be found")
    if errors:
        raise AssertionError("One or more languages was not installed as "
                             "expected\n\t%s" % "\n\t".join(errors))
    if _is_win:  # pragma: windows
        if os.environ.get('HOMEDRIVE', None):
            assert os.path.expanduser('~').startswith(os.environ['HOMEDRIVE'])
        else:
            assert os.path.expanduser('~').lower().startswith('c:')


def log_environment(new_filename='new_environment_log.txt',
                    old_filename='old_environment_log.txt'):
    r"""Create a record of the Python package versions.

    Args:
        new_filename (str, optional): Name of the file where the
            environment information should be stored. Defaults to
            'new_environment_log.txt'.
        old_filename (str, optional): Name of the file where previous
            environment information is stored for diff. Defaults to
            'old_environment_log.txt'.

    """
    if os.path.isfile(new_filename):
        if os.path.isfile(old_filename):
            raise RuntimeError("Package list already exists: '%s'"
                               % new_filename)
        else:
            shutil.move(new_filename, old_filename)
    now = datetime.now()
    cmds = ["echo \"%s\" >> %s" % (now.strftime("%Y/%m/%d %H:%M:%S"),
                                   new_filename),
            "%s --version >> %s" % (PYTHON_CMD, new_filename),
            "%s -m pip list >> %s" % (PYTHON_CMD, new_filename)]
    if shutil.which('conda'):
        cmds.append(f"{CONDA_CMD} list >> {new_filename}")
    call_script(cmds)
    assert os.path.isfile(new_filename)
    if os.path.isfile(old_filename):
        with open(new_filename, 'r') as fd:
            new_contents = fd.read()
        with open(old_filename, 'r') as fd:
            old_contents = fd.read()
        diff = difflib.ndiff(old_contents.splitlines(),
                             new_contents.splitlines())
        print('\n'.join(diff))


if __name__ == "__main__":
    install_opts = get_install_opts()
    parser = argparse.ArgumentParser(
        "Perform setup operations to test package build and "
        "installation on continuous integration services.")
    subparsers = parser.add_subparsers(
        dest='operation',
        help="CI setup operation that should be performed.")
    # Environment creation
    parser_env = subparsers.add_parser(
        'env', help="Setup an environment for testing.")
    parser_env.add_argument(
        'method', choices=['conda', 'virtualenv', 'mamba'],
        help=("Method that should be used to create "
              "the test environment."))
    parser_env.add_argument(
        'python',
        help="Version of python that should be tested.")
    parser_env.add_argument(
        '-n', '--env-name', default=None,
        help="Name that should be used for the environment.")
    parser_env.add_argument('--use-mamba', action='store_true',
                            help="Use mamba in place of conda")
    # Build package
    parser_bld = subparsers.add_parser(
        'build', help="Build the package.")
    parser_bld.add_argument(
        'method', choices=['conda', 'pip', 'mamba'],
        help=("Method that should be used to build the package."))
    parser_bld.add_argument(
        '--python', default=None,
        help="Version of python that package should be built for.")
    parser_bld.add_argument(
        '--verbose', action='store_true',
        help="Turn up verbosity of output.")
    parser_bld.add_argument('--use-mamba', action='store_true',
                            help="Use mamba in place of conda")
    # Install dependencies
    parser_dep = subparsers.add_parser(
        'deps', help="Install the package dependencies.")
    parser_dep.add_argument(
        'method', choices=['conda', 'pip', 'mamba'],
        help=("Method that should be used to install the package dependencies."))
    parser_dep.add_argument(
        '--dry-run', action='store_true',
        help="Don't actually install any dependencies.")
    SetupParam.add_parser_args(parser_dep)
    # Install package
    parser_pkg = subparsers.add_parser(
        'install', help="Install the package.")
    parser_pkg.add_argument(
        'method', choices=['conda', 'pip', 'mamba',
                           'conda-dev', 'pip-dev', 'mamba-dev'],
        help=("Method that should be used to install the package."))
    parser_pkg.add_argument(
        '--python', default=None,
        help="Version of python that package should be built/installed for.")
    parser_pkg.add_argument(
        '--without-build', action='store_true',
        help=("Perform installation steps without building first. (Assumes "
              "the package has already been built)."))
    parser_pkg.add_argument(
        '--without-deps', action='store_true',
        help=("Perform installation steps without installing dependencies first. "
              "(Assumes they have already been installed)."))
    SetupParam.add_parser_args(parser_pkg, skip=['target_os'])
    # Installation verification
    parser_ver = subparsers.add_parser(
        'verify', help="Verify that the package was installed correctly.")
    add_install_opts_args(parser_ver, install_opts=install_opts)
    # Environment logging
    parser_log = subparsers.add_parser(
        'log', help="Create a log of the Python environment.")
    parser_log.add_argument(
        '--new-filename', default='new_environment_log.txt',
        help="File where the new environment log should be saved.")
    parser_log.add_argument(
        '--old-filename', default='old_environment_log.txt',
        help=("File containing previous environment log that the new "
              "log should be diffed against."))
    # Create environment.yml
    parser_yml = subparsers.add_parser(
        'env-yaml', help="Create an environment.yml file.")
    parser_yml.add_argument(
        '--filename', default='environment.yml',
        help="File where the environment yaml should be saved.")
    parser_yml.add_argument(
        '--name', '-n', default='ygg',
        help="Name of environment.")
    parser_yml.add_argument(
        '--channels', '--channel', '-c', nargs='*',
        help="Name of conda channels that should be used.")
    parser_yml.add_argument(
        '--python-version', '--python', type=str,
        help="Python version that environment should use.")
    SetupParam.add_parser_args(parser_yml, skip=['conda_env'],
                               no_install=True)
    # Call methods
    args = parser.parse_args()
    if args.operation in ['deps', 'install', 'verify', 'env-yaml']:
        SetupParam.extract_install_opts_from_args(args, install_opts)
    if args.operation in ['env', 'setup']:
        create_env(args.method, args.python, name=args.env_name,
                   use_mamba=args.use_mamba)
    elif args.operation == 'build':
        build_pkg(args.method, python=args.python,
                  verbose=args.verbose, use_mamba=args.use_mamba)
    elif args.operation == 'deps':
        install_deps(args.method, verbose=args.verbose,
                     for_development=args.for_development,
                     windows_package_manager=args.windows_package_manager,
                     install_opts=install_opts,
                     conda_env=args.conda_env, always_yes=args.always_yes,
                     only_python=args.only_python, use_mamba=args.use_mamba,
                     dry_run=args.dry_run, do_preinstall=True)
    elif args.operation == 'install':
        install_pkg(args.method, python=args.python,
                    without_build=args.without_build,
                    without_deps=args.without_deps,
                    verbose=args.verbose,
                    windows_package_manager=args.windows_package_manager,
                    install_opts=install_opts,
                    conda_env=args.conda_env, always_yes=args.always_yes,
                    only_python=args.only_python,
                    use_mamba=args.use_mamba)
    elif args.operation == 'verify':
        verify_pkg(install_opts=install_opts)
    elif args.operation == 'log':
        log_environment(new_filename=args.new_filename,
                        old_filename=args.old_filename)
    elif args.operation == 'env-yaml':
        install_opts['os'] = args.target_os
        create_env_yaml(filename=args.filename, name=args.name,
                        channels=args.channels, target_os=args.target_os,
                        python_version=args.python_version,
                        for_development=args.for_development,
                        install_opts=install_opts,
                        use_mamba=args.use_mamba)
