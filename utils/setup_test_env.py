import os
import sys
import argparse
import uuid
import pprint
import shutil
import subprocess
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
_is_win = (sys.platform in ['win32', 'cygwin', 'msys'])
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
except AttributeError:
    if _is_win:
        CONDA_CMD_WHICH = None
    else:
        try:
            CONDA_CMD_WHICH = subprocess.check_output(
                ['which', 'conda']).strip().decode('utf-8')
        except subprocess.CalledProcessError:
            CONDA_CMD_WHICH = None
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
        env_created (bool, optional): If True, the env is assumed to
            not yet exist as it will be created. Defaults to False.
        **kwargs: Additional keyword arguments are parsed according to
            the values specified in _args.

    """

    _args = [
        ('method', [], {
            'choices': ['conda', 'pip', 'mamba'],
            'help': "Method that should be used to install packages"}),
        (('--env-method', ), ['auto'], {
            'choices': ['conda', 'mamba', 'virtualenv', None],
            'default': None,
            'help': ("Method that should be used to create an "
                     "environment")}),
        (('--python', '--python-version'), [], {
            'type': str,
            'help': "Python version that should be installed"}),
        ('--target-os', [], {
            'choices': ['win', 'osx', 'linux'],
            'default': None,
            'help': ("Operating system that should be targeted if "
                     "different from the current OS.")}),
        ('--for-development', ['install'], {
            'action': 'store_true',
            'help': ("Install dependencies used during development "
                     "and that would be missed when installing in "
                     "development mode.")}),
        ('--windows-package-manager', ['install'], {
            'default': 'vcpkg',
            'choices': ['vcpkg', 'choco'],
            'help': "Package manager that should be used on Windows."}),
        (('--env-name', '-n', '--name'), [], {
            'default': None,
            'help': ("Conda or virtualenv environment that packages "
                     "should be installed in.")}),
        ('--verbose', ['run'], {
            'action': 'store_true',
            'help': "Turn up verbosity of output."}),
        ('--always-yes', ['run'], {
            'action': 'store_true',
            'help': "Don't ask for user input to run commands."}),
        (('--only-python', '--python-only'), ['install'], {
            'action': 'store_true',
            'help': "Only install python dependencies."}),
        ('--use-mamba', [], {
            'action': 'store_true',
            'help': "Use mamba in place of conda"}),
        ('--user', ['run', 'install'], {
            'action': 'store_true',
            'help': "Install in user mode."}),
        ('--dry-run', ['run'], {
            'action': 'store_true',
            'help': "Don't actually run any commands"}),
        ('--deps-method', ['install'], {
            'type': str,
            'choices': ["all", "env", "unique", "supplemental",
                        "conda_recipe"],
            'default': 'env',
            'help': (
                "How the method should be used to select"
                " dependencies. Options:\n"
                "    all: Do not deselect any dependencies based"
                " on their method.\n"
                "    env: Select dependencies with methods"
                " that are valid for the select environment.\n"
                "    unique: Select dependencies that can only be"
                " installed by the specified method.\n"
                "    supplemental: Select dependencies that cannot"
                " be installed by the specified method.\n"
                "    conda_recipe: Select dependencies that would"
                " occur in a conda recipe.")}),
        ('--fallback-to-conda', ['install'], {
            'action': 'store_true',
            'default': None,
            'help': ("Fallback to installing non-python dependencies "
                     "using mamba/conda")}),
    ]

    def __init__(self, method=None, install_opts=None,
                 env_created=False, **kwargs):
        self.method = method
        self.install_opts = get_install_opts(install_opts)
        for k in self.args_to_copy():
            if k in kwargs:
                setattr(self, k, kwargs.pop(k))
            else:
                setattr(self, k, self.get_default(k))
        assert not kwargs
        self.conda_flags = ''
        self.pip_flags = ''
        if not self.python:
            self.python = PYVER
        # Modified inputs vars:
        #   use_mamba, method, fallback_to_conda, install_opts,
        #   target_os
        if self.target_os is None:
            self.target_os = self.install_opts['os']
        else:
            assert self.target_os in ['linux', 'osx', 'win', 'any']
            if self.target_os != self.install_opts['os']:
                assert self.dry_run
            self.install_opts['os'] = self.target_os
        if self.method is None:
            if self.use_mamba:
                self.method = 'conda'
            elif self.env_method in ('conda', 'mamba'):
                self.method = self.env_method
            elif self.env_method == 'virtualenv':
                self.method = 'pip'
            elif CONDA_ENV:
                self.method = 'conda'
            else:
                self.method = 'pip'
        elif self.method.startswith('mamba'):
            self.use_mamba = True
            self.method = self.method.replace('mamba', 'conda')
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
        if self.fallback_to_conda is None:
            self.fallback_to_conda = ((self.method_base == 'conda')
                                      or (_is_win and _on_appveyor)
                                      or self.install_opts['lpy'])
        if self.env_method is None:
            if self.fallback_to_conda:
                if self.use_mamba:
                    self.env_method = 'mamba'
                else:
                    self.env_method = 'conda'
            else:
                self.env_method = 'virtualenv'
        if self.env_name and self.env_method in ('conda', 'mamba'):
            self.conda_env = self.env_name
        else:
            self.conda_env = None
        self.python_cmd = PYTHON_CMD
        if self.conda_env:
            self.python_cmd = locate_conda_exe(
                self.conda_env, 'python',
                allow_missing=env_created,
                use_mamba=self.use_mamba)
            self.conda_flags += f' --name {self.conda_env}'
        if self.for_development:
            self.install_opts['dev'] = True
        # Methods that can be used to install deps
        self.valid_methods = ['skip']
        if self.deps_method == 'all':
            self.valid_methods += ['python', 'pip', 'pip_skip',
                                   'conda', 'conda_skip', 'cran',
                                   'brew', 'apt', 'choco', 'vcpkg']
        elif self.deps_method in ['env', 'supplemental']:
            self.valid_methods += ['python', 'pip', 'pip_skip']
            if self.fallback_to_conda:
                self.valid_methods += ['conda', 'conda_skip']
            elif not self.only_python:
                self.valid_methods.append('cran')
                if self.install_opts['os'] == 'linux':
                    self.valid_methods.append('apt')
                elif self.install_opts['os'] == 'osx':
                    self.valid_methods.append('brew')
                elif self.install_opts['os'] == 'win':
                    self.valid_methods.append(self.windows_package_manager)
                    if 'vcpkg' not in self.valid_methods:
                        self.valid_methods.append('vcpkg')
            if self.deps_method == 'supplemental':
                if not (self.for_development or self.method == 'pip'):
                    # Pip extras installed directly as extras do not
                    # seem to work when installing from a sdist
                    for k in ['python', self.method_base,
                              f'{self.method_base}_skip']:
                        if k in self.valid_methods:
                            self.valid_methods.remove(k)
                self.valid_methods.append(f"{self.method_base}_supp")
        elif self.deps_method == 'unique':
            self.valid_methods += [f'{self.method_base}_skip',
                                   self.method_base]
        elif self.deps_method == 'conda_recipe':
            self.valid_methods += ['conda', 'conda_skip',
                                   'conda_recipe', 'python']
        if self.only_python:
            for k in ['cran', 'apt', 'brew', 'choco', 'vcpkg']:
                if k in self.valid_methods:
                    self.valid_methods.remove(k)
        # print(f"deps_method = {self.deps_method}, "
        #       f"valid_methods = {self.valid_methods}")

    @classmethod
    def find_args(cls, x):
        x_try = [x, '--' + x.replace('_', '-')]
        for k, types, v in cls._args:
            if isinstance(k, tuple):
                if any(xx in k for xx in x_try):
                    return (k, types, v)
            else:
                if k in x_try:
                    return (k, types, v)
        raise KeyError(x)

    @classmethod
    def get_default(cls, x):
        k, types, v = cls.find_args(x)
        if 'default' in v:
            return v['default']
        if v.get('action', None) == 'store_true':
            return False
        return None

    @classmethod
    def args_to_copy(cls, keep_method=False):
        r"""list: Arguments to copy."""
        out = []
        for x in cls._args:
            base = x[0]
            if isinstance(base, tuple):
                base = base[0]
            out.append(base.lstrip('-').replace('-', '_'))
        if not keep_method:
            out.remove('method')
        return out

    @classmethod
    def from_args(cls, args, install_opts, env_created=False,
                  require_env_name=False, **kwargs):
        if env_created:
            require_env_name = True
        method = getattr(args, 'method', None)
        if require_env_name and getattr(args, 'env_name', None) is None:
            assert method is not None
            args.env_name = method + args.python.replace('.', '')
        cls.extract_install_opts_from_args(args, install_opts)
        for k in cls.args_to_copy():
            if hasattr(args, k):
                kwargs[k] = getattr(args, k)
        kwargs['env_created'] = env_created
        return cls(method=method, install_opts=install_opts, **kwargs)

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
    def add_parser_args(parser, skip=None, skip_types=None,
                        skip_all=False, include=None,
                        install_opts=None, additional_args=None,
                        **kwargs):
        r"""Add arguments to a parser for installation options.

        Args:
            parser (argparse.ArgumentParser): Parser to add arguments to.
            skip_all (bool, optional): If True, only install_opts
                will be added. Defaults to False.
            skip (list, optional): Arguments that should not be added.
                Defaults to an empty list.
            skip_types (list, optional): Type of argument that should
                be skipped. Defaults to an empty list.
            include (list, optional): Arguments that should be included
                even if the type if skipped. Defaults to an empty list.
            install_opts (dict, optional): Existing installation options
                that should be used to set the flags. Create using
                get_install_opts if not provided.
            additional_args (list, optional): Additional arguments that
                should be added after positional arguments.
            **kwargs: Additional keyword arguments are checked for
                parameters pertaining to individual arguments.

        """
        if skip is None:
            skip = []
        if skip_types is None:
            skip_types = []
        skip_types.append('auto')
        if include is None:
            include = []

        def args_match(a_args, match):
            for x in a_args:
                x = x.strip('-')
                if x in match or x.replace('-', '_') in match:
                    return True
            return False

        args_req = []
        args_opt = []

        def add_argument(*a_args, **a_kwargs):
            base = a_args[0].lstrip('-').replace('-', '_')
            if f"{base}_args" in kwargs:
                a_args = kwargs.pop(f"{base}_args")
                a_kwargs['dest'] = base
            for k in ['choices', 'default', 'help']:
                if f"{base}_{k}" in kwargs:
                    a_kwargs[k] = kwargs.pop(f"{base}_{k}")
            if kwargs.pop(f"{base}_optional", False):
                assert not any(x.startswith('--') for x in a_args)
                a_args = tuple(['--' + x for x in a_args])
            if kwargs.pop(f"{base}_required", False):
                assert all(x.startswith('--') for x in a_args)
                a_args = (base, )
            # if additional_args and a_args[0].startswith('--'):
            #     for kk, vv in additional_args:
            #         parser.add_argument(*kk, **vv)
            #     additional_args.clear()
            if a_args[0].startswith('--'):
                args_opt.append((a_args, a_kwargs))
            else:
                args_req.append((a_args, a_kwargs))
            # parser.add_argument(*a_args, **a_kwargs)

        if skip_all:
            if include:
                for k, types, v in SetupParam._args:
                    if not isinstance(k, tuple):
                        k = (k, )
                    if args_match(k, include):
                        add_argument(*k, **v)
        else:
            for k, types, v in SetupParam._args:
                if not isinstance(k, tuple):
                    k = (k, )
                if (((any(x in types for x in skip_types)
                      or args_match(k, skip))
                     and not args_match(k, include))):
                    continue
                add_argument(*k, **v)
        if additional_args:
            for k, v in additional_args:
                if k[0].startswith('--'):
                    args_opt.append((k, v))
                else:
                    args_req.append((k, v))
        for k, v in args_req + args_opt:
            parser.add_argument(*k, **v)
        if kwargs:
            pprint.pprint(kwargs)
        assert not kwargs  # Use all keyword arguments
        add_install_opts_args(parser, install_opts=install_opts)


def get_summary_commands(param=None, **kwargs):
    r"""Get commands to use to summarize the state of the environment.

    Args:
        use_mamba (bool, optional): If True, use mamba in place of conda.
        param (SetupParam, optional): Parameters controlling setup. If
            not provided, parameters will be generated from kwargs.
        **kwargs: Keyword arguments are passed to SetupParam if param
            is not provided.

    Returns:
        list: Commands.

    """
    if param is None:
        param = SetupParam(**kwargs)
    out = [f"{param.python_cmd} --version",
           f"{param.python_cmd} -m pip list"]
    if CONDA_ENV:
        flags = ''
        if param.conda_env:
            flags = f'--name {param.conda_env}'
        out += [f"echo 'CONDA_PREFIX={CONDA_PREFIX}'",
                f"{param.conda_exe} info",
                f"{param.conda_exe} list {flags}",
                f"{param.conda_exe_config} config --show-sources"]
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


def call_script(lines, force_bash=False, verbose=False, dry_run=False,
                call_kws=None):
    r"""Write lines to a script and call it.

    Args:
        lines (list): Lines that should be written to the script.
        force_bash (bool, optional): If True, bash will be used, even
            on windows. Defaults to False.
        verbose (bool, optional): If True, each line will be printed before
            it is executed.
        dry_run (bool, optional): If True, don't actually run any
            commands. Defaults to False.
        call_kws (dict, optional): Keyword arguments that should be
            passed to the subprocess call.

    """
    # if _on_gha:
    verbose = True
    if call_kws is None:
        call_kws = {}
    if dry_run:
        lines_str = '\n\t'.join(lines)
        print(f"Dry run:\n\t{lines_str}")
        return
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
    if conda_env is None:
        conda_env = CONDA_ENV
    assert CONDA_ROOT
    conda_prefix = os.path.join(CONDA_ROOT, 'envs')
    if sys.platform in ['win32', 'cygwin']:
        out = os.path.join(conda_prefix, conda_env, 'Scripts')
    else:
        out = os.path.join(conda_prefix, conda_env, 'bin')
    return out


def locate_exe(name):
    r"""Locate an executable.

    Args:
        name (str): Name of the executable to locate.

    Returns:
        str: Full path to the executable.

    """
    try:
        return shutil.which('yggdrasil')
    except AttributeError:
        try:
            return subprocess.check_output(
                ['which', 'yggdrasil']).strip().decode('utf-8')
        except subprocess.CalledProcessError:
            pass
    return None


def locate_conda_exe(conda_env, name, use_mamba=False,
                     allow_missing=False):
    r"""Determine the full path to an executable in a specific conda
    environment.

    Args:
        conda_env (str): Name of conda environment that executable
            should be returned for.
        name (str): Name of the executable to locate.
        use_mamba (bool, optional): If True, use mamba in place of
            conda.
        allow_missing (bool, optional): If True, don't raise an error
            if the executable dosn't exist. Defaults to False.

    Returns:
        str: Full path to the executable.

    """
    if sys.platform in ['win32', 'cygwin'] and not name.endswith('.exe'):
        name += '.exe'
    out = os.path.join(
        locate_conda_bin(conda_env, use_mamba=use_mamba), name)
    if sys.platform in ['win32', 'cygwin'] and name.startswith('python'):
        out = os.path.dirname(out)
    if allow_missing:
        return out
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


def create_env(env_method, python, param=None, name=None, packages=None,
               init=_on_ci, populate=False, **kwargs):
    r"""Setup an environment for yggdrasil installation.

    Args:
        env_method (str): Method that should be used to create an
            environment. Supported values currently include 'conda',
            'mamba', and 'virtualenv'.
        python (str): Version of Python that should be tested.
        param (SetupParam, optional): Parameters defining setup. If
            not provided, one will be created from kwargs.
        name (str, optional): Name that should be used for the
            environment. Defaults to None and will be craeted based
            on the method and Python version.
        packages (list, optional): Packages that should be installed
            in the new environment. Defaults to None and is ignored.
        init (bool, optional): If True, the environment management
            program is first configured as if it is on CI so that some
            interactive aspects will be disabled. Default is set based
            on the presence of CI environment variables (it currently
            checks for Github Actions, Travis CI, and Appveyor).
        populate (bool, optional): If True, the environment will be
            populated. Defaults to False.

    """
    if param is None:
        if name:
            kwargs['env_name'] = name
        param = SetupParam(env_method=env_method, python=python,
                           **kwargs)
    python = param.python
    if name is None:
        name = param.env_name
    if name is None:
        name = env_method + python.replace('.', '')
    cmds = [f"echo Creating test environment using {env_method}..."]
    major, minor = [int(x) for x in python.split('.')][:2]
    if packages is None:
        packages = []
    # if 'requests' not in packages:
    #     # Not strictly required, but useful for determine the versions of
    #     # dependencies required by packages during testing
    #     packages.append('requests')
    if param.env_method in ('conda', 'mamba'):
        conda_exe_config = param.conda_exe_config
        conda_exe = param.conda_exe
        if (((not param.dry_run)
             and conda_env_exists(name, use_mamba=param.use_mamba))):
            print(f"Conda env with name '{name}' already exists.")
            if not populate:
                return
        else:
            if init:
                cmds += [
                    # Configure conda
                    f"{conda_exe_config} config --set always_yes yes --set changeps1 no",
                    f"{conda_exe_config} config --set channel_priority strict",
                    f"{conda_exe_config} config --prepend channels conda-forge",
                    f"{conda_exe_config} update -q {param.env_method}",
                    # f"{conda_exe_config} config --set allow_conda_downgrades true",
                    # f"{conda_exe} install -n root conda=4.9",
                ]
            cmds += [
                (f"{conda_exe} create -q -n {name} python={python} "
                 + ' '.join(packages))
            ]
    elif param.env_method == 'virtualenv':
        python_cmd = param.python_cmd
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
                raise RuntimeError(
                    f"The version of Python "
                    f"{sys.version_info[0]}.{sys.version_info[1]}) "
                    f"does not match the desired version "
                    f"({param.python}) and virtualenv cannot create "
                    f"an environment with a different version of "
                    f"Python.")
        cmds += [
            f"{python_cmd} -m pip install --upgrade pip virtualenv",
            f"virtualenv -p {python_cmd} {name}"
        ]
        if populate or packages:
            if param.target_os == 'win':
                cmds.append(f".\\{name}\\Scripts\\activate")
            else:
                cmds.append(f"source {name}/bin/activate")
        if packages:
            cmds.append(f"{python_cmd} -m pip install " + ' '.join(packages))
    else:  # pragma: debug
        raise ValueError(f"Unsupported environment management method:"
                         f" '{param.env_method}'")
    if populate:
        cmds += install_pkg(param.method, param=param,
                            return_commands=True)
    call_script(cmds, verbose=param.verbose,
                dry_run=param.dry_run)


def build_pkg(method, param=None, return_commands=False, **kwargs):
    r"""Build the package on a CI resource.

    Args:
        method (str): Method that should be used to build the package.
            Valid values include 'conda', 'mamba', and 'pip'.
        param (SetupParam, optional): Parameters defining setup. If
            not provided, one will be created from kwargs.
        return_commands (bool, optional): If True, the commands
            necessary to build the package are returned instead of
            running them. Defaults to False.
        **kwargs: Additional keyword arguments are passed to
            SetupParam.

    """
    if param is None:
        param = SetupParam(method, **kwargs)
    cmds = []
    # Upgrade pip and setuptools and wheel to get clean install
    upgrade_pkgs = ['wheel', 'setuptools']
    if not _is_win:
        upgrade_pkgs.insert(0, 'pip')
    if param.method == 'conda':
        conda_env = CONDA_ENV
        conda_idx = CONDA_INDEX
        if param.use_mamba:
            conda_build = f"{CONDA_CMD} mambabuild"
            build_pkgs = ["boa"]
        else:
            conda_build = f"{CONDA_CMD} build"
            build_pkgs = ["conda-build", "conda-verify"]
        if param.verbose:
            build_flags = ''
        else:
            build_flags = '-q'
        # Must always build in base to avoid errors (and don't change the
        # version of Python used in the environment)
        # https://github.com/conda/conda/issues/9124
        # https://github.com/conda/conda/issues/7758#issuecomment-660328841
        assert conda_env == 'base' or param.dry_run
        assert conda_idx
        if _on_gha:
            cmds += [
                f"{param.conda_exe_config} config --prepend channels"
                f" conda-forge",
                f"{param.conda_exe} update -q {param.method}",
            ]
        if _is_win and _on_gha:
            # The tests issue a command that is too long for the
            # windows command prompt which is used to build the conda
            # package on Github Actions
            build_flags += ' --no-test'
        cmds += [
            f"{param.conda_exe} clean --all"]  # Might invalidate cache
        if not (_is_win and _on_gha):
            cmds += [f"{param.conda_exe} update --all"]
        cmds += [
            f"{param.conda_exe} install -q -n base " + ' '.join(build_pkgs),
            f"{conda_build} recipe --python {param.python} {build_flags}"
        ]
        cmds.append(f"{param.conda_exe} index {conda_idx}")
    elif param.method == 'pip':
        if param.verbose:
            build_flags = ''
        else:
            build_flags = '--quiet'
        # Install from source dist
        cmds += [f"{param.python_cmd} -m pip install --upgrade "
                 + ' '.join(upgrade_pkgs)]
        cmds += [f"{param.python_cmd} setup.py {build_flags} sdist"]
    else:  # pragma: debug
        raise ValueError(f"Method must be 'conda', 'mamba', or 'pip', not"
                         f" '{param.method}'")
    summary_cmds = get_summary_commands(param)
    if cmds:
        cmds += summary_cmds
    if return_commands:
        return cmds
    if cmds:
        cmds = summary_cmds + cmds
        if param.use_mamba and not shutil.which('mamba'):
            cmds_after = cmds
            cmds = get_summary_commands()
            cmds += [
                f"{CONDA_CMD} config --prepend channels conda-forge",
                f"{CONDA_CMD} config --remove channels defaults",
                f"{CONDA_CMD} config --set channel_priority strict",
            ]
            if not (_is_win and _on_gha):
                cmds += [f"{CONDA_CMD} update --all"]
            cmds += [f"{CONDA_CMD} install mamba -c conda-forge"]
            cmds += cmds_after
        call_script(cmds, verbose=param.verbose,
                    dry_run=param.dry_run)
    if param.method == 'conda':  # and not param.use_mamba:
        print(f"CONDA_IDX = {conda_idx}")
        assert (conda_idx and os.path.isdir(conda_idx))


def preinstall_deps(method, param=None, return_commands=False,
                    no_packages=False, **kwargs):
    r"""Pre-install packages with test specific versions.

    Args:
        method (str): Method that should be used to install the
            package dependencies. Valid values include 'conda',
            'mamba', and 'pip'.
        param (SetupParam, optional): Parameters defining setup. If
            not provided, one will be created from kwargs.
        return_commands (bool, optional): If True, the commands
            necessary to install the dependencies are returned instead
            of running them. Defaults to False.
        no_package (bool, optional): If True, no packages are
            uninstalled or installed. Defaults to False.
        **kwargs: Additional keyword arguments are passed to
            SetupParam.

    """
    if param is None:
        param = SetupParam(method, **kwargs)
    conda_prefix = '$CONDA_PREFIX'
    conda_root = CONDA_ROOT
    cmds = []
    # Uninstall default numpy and matplotlib to allow installation
    # of specific versions
    if not no_packages:
        # Installing via pip causes import error on Windows and
        #  a conflict when installing LPy
        # TODO: Get this from YggRequirements
        version_specified = ['scipy', 'numpy',
                             'matplotlib', 'jsonschema']
        if param.method != 'conda':
            cmds += [f"{param.python_cmd} -m pip uninstall -y "
                     + ' '.join(version_specified)]
    # Refresh channel
    # https://github.com/conda/conda/issues/8051
    if param.fallback_to_conda and _on_gha:
        cmds += [
            f"{param.conda_exe_config} config --set channel_priority strict",
            # These commands will not be valid for mamba
            # f"{param.conda_exe} install -n root conda=4.9",
            # f"{param.conda_exe_config} config --set "
            # f" allow_conda_downgrades true",
            f"{param.conda_exe_config} config --remove channels conda-forge",
            f"{param.conda_exe_config} config --prepend channels conda-forge",
        ]
    if param.fallback_to_conda and not no_packages:
        cmds.append(f"{param.conda_exe} update --all")
    if _on_gha and _is_unix and param.fallback_to_conda:
        if param.conda_env:
            conda_prefix = os.path.join(conda_root, 'envs',
                                        param.conda_env)
        # Do both to ensure that the path is set for the installation
        # and in following steps
        cmds += [
            f"export LD_LIBRARY_PATH={conda_prefix}/lib:$LD_LIBRARY_PATH",
            "echo -n \"LD_LIBRARY_PATH=\" >> $GITHUB_ENV",
            f"echo {conda_prefix}/lib:$LD_LIBRARY_PATH >> $GITHUB_ENV"
        ]
    if return_commands:
        return cmds
    if cmds:
        cmds += get_summary_commands(param)
        call_script(cmds, verbose=param.verbose,
                    dry_run=param.dry_run)


def install_deps(method, param=None, return_commands=False,
                 do_preinstall=False, req=None, **kwargs):
    r"""Install the package dependencies.
    
    Args:
        method (str): Method that should be used to install the
            package dependencies. Valid values include 'conda',
            'mamba', and 'pip'.
        param (SetupParam, optional): Parameters defining setup. If
            not provided, one will be created from kwargs.
        return_commands (bool, optional): If True, the commands
            necessary to install the dependencies are returned instead
            of running them. Defaults to False.
        do_preinstall (bool, optional): If True, steps are taken to
            prepare for installation. Defaults to False.
        req (YggRequirements, optional): Existing set of requirements
            to use.
        **kwargs: Additional keyword arguments are passed to
            SetupParam.

    """
    from manage_requirements import install_requirements
    if param is None:
        kwargs.setdefault("deps_method", "supplemental")
        param = SetupParam(method, **kwargs)
    cmds = []
    if do_preinstall:
        cmds += preinstall_deps(param.method_base, param=param,
                                return_commands=True)
        if cmds:
            cmds += get_summary_commands(param)
    cmds += install_requirements(param,
                                 return_commands=True,
                                 req=req)
    summary_cmds = get_summary_commands(param=param)
    if cmds:
        cmds += summary_cmds
    if return_commands:
        return cmds
    if cmds:
        cmds = summary_cmds + cmds
        call_script(cmds, verbose=param.verbose,
                    dry_run=param.dry_run)
    return cmds


def install_pkg(method, param=None, without_build=False,
                without_deps=False, install_deps_before=False,
                return_commands=False, **kwargs):
    r"""Build and install the package and its dependencies on a CI
    resource.

    Args:
        method (str): Method that should be used to build and install
            the package. Valid values include 'conda' and 'pip'.
        param (SetupParam, optional): Parameters defining setup. If
            not provided, one will be created from kwargs.
        without_build (bool, optional): If True, the package will not
            be built prior to install. Defaults to False.
        without_deps (bool, optional): If True the package
            dependencies will not be installed prior to installing
            the package. Defaults to False.
        install_deps_before (bool, optional): If True, install deps
            before the package is installed. Set to true in the case
            of pip or dev environments to handle non-Python
            dependencies before yggdrasil is installed. Defaults to
            False.
        return_commands (bool, optional): If True, the commands
            necessary to install the package are returned instead of
            running them. Defaults to False.
        **kwargs: Additional keyword arguments are passed to
            SetupParam.

    Raises:
        ValueError: If method is not 'conda' or 'pip'.

    """
    from manage_requirements import YggRequirements
    if param is None:
        param = SetupParam(method, **kwargs)
    if param.method != 'conda' and not param.only_python:
        # For pip and dev environments, non-Python deps should be
        #   installed before yggdrasil
        install_deps_before = True
    summary_cmds = get_summary_commands(param)
    cmds = [x for x in summary_cmds]  # Make sure this a copy
    if param.for_development:
        without_build = True
    if not without_build:
        cmds += build_pkg(param.method, param=param,
                          return_commands=True)
    cmds_deps = []
    cmds += preinstall_deps(param.method_base,
                            param=param,
                            return_commands=True)
    req = YggRequirements.from_file()
    if not without_deps:
        cmds_deps += install_deps(param.method_base, param=param,
                                  return_commands=True, req=req)
    if install_deps_before:
        cmds += cmds_deps
    extras = [
        x for x in req.extras(methods=['python', param.method_base])
        if param.install_opts[x]]
    # Install yggdrasil
    if param.for_development:
        # Call setup.py in separate process from the package directory
        # cmds += [f"{param.python_cmd} setup.py develop"]
        pass
    elif param.method == 'conda':
        conda_exe_config = CONDA_CMD
        if param.use_mamba:
            conda_exe = MAMBA_CMD
            conda_idx = CONDA_INDEX  # 'local'
        else:
            conda_exe = CONDA_CMD
            conda_idx = CONDA_INDEX
        if not (conda_idx and os.path.isdir(conda_idx)):
            print(f"conda_idx = {conda_idx}")
        assert (conda_idx and os.path.isdir(conda_idx))
        # Install from conda build
        # Assumes that the target environment is active
        install_flags = param.conda_flags
        if not param.use_mamba:
            install_flags += ' --update-deps'
        if _is_win:
            index_channel = conda_idx
        else:
            index_channel = f"file:/{conda_idx}"
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
        if 'mpi' in extras:
            assert ' install ' in cmds[-1]
            cmds[-1] += " # [ALLOW FAIL]"
        cmds += summary_cmds
    elif param.method == 'pip':
        if _is_win:  # pragma: windows
            cmds += [
                "for %%a in (\"dist\\*.tar.gz\") do set YGGSDIST=%%a",
                "echo %YGGSDIST%"
            ]
            sdist = "%YGGSDIST%"
        else:
            sdist = "dist/*.tar.gz"
        # if extras:
        #     sdist += f"[{','.join(extras)}]"
        cmds += [
            f"{param.python_cmd} -m pip install"
            f" {param.pip_flags} {sdist}",
            f"{param.python_cmd} create_coveragerc.py"
        ]
        cmds += summary_cmds
    else:  # pragma: debug
        raise ValueError(f"Invalid method: '{param.method}'")
    yggdrasil_installed = False
    if param.method == 'conda':
        try:
            locate_conda_exe(param.conda_env, 'yggdrasil',
                             use_mamba=param.use_mamba)
            yggdrasil_installed = True
        except AssertionError:
            pass
    else:
        yggdrasil_installed = (locate_exe('yggdrasil') is not None)
    if yggdrasil_installed and not param.dry_run:
        cmds = []
    if not install_deps_before:
        cmds += cmds_deps
    if (((param.dry_run or (not yggdrasil_installed))
         and param.for_development)):
        src = '.'
        if extras:
            src += f"[{','.join(extras)}]"
        cmds += [
            f"cd {_pkg_dir}",
            f"{param.python_cmd} -m pip install --editable {src}",
            f"cd {os.getcwd()}"]
    # Follow up if on Unix as R installation may require sudo
    if param.install_opts['r'] and _is_unix:
        # TODO: Fix location of R executable
        R_cmd = f"{param.python_cmd} -m yggdrasil install r"
        if not param.install_opts['no_sudo']:
            R_cmd += ' --sudoR'
        cmds.append(R_cmd)
    call_kws = {}
    if param.method == 'conda':
        env = copy.copy(os.environ)
        if (not param.install_opts['no_sudo']) and param.install_opts['r']:
            env['YGG_USE_SUDO_FOR_R'] = '1'
        src_dir = os.path.join(os.getcwd(),
                               os.path.dirname(os.path.dirname(__file__)))
        cmds += [
            f"cd {src_dir}",
            f"{param.python_cmd} create_coveragerc.py",
            f"cd {os.getcwd()}"]
        call_kws['env'] = env
    if return_commands:
        return cmds
    call_script(cmds, verbose=param.verbose, dry_run=param.dry_run,
                call_kws=call_kws)


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
    SetupParam.add_parser_args(
        parser_env,
        env_method_required=True,
        python_required=True,
        env_name_help="Name that should be used for the environment.",
        include=['env_method'],
        skip=['target_os', 'method'],
        skip_types=['install'])
    # Development environment setup
    parser_dev = subparsers.add_parser(
        'devenv',
        help=("Create and populated a development environment "
              "for testing yggdrasil."))
    SetupParam.add_parser_args(
        parser_dev,
        python_required=True,
        include=['env_method'],
        env_method_default='mamba',
        env_name_help="Name that should be used for the environment.",
        skip=['for_development', 'deps_method', 'user'])
    # Multiple env creation
    parser_devmat = subparsers.add_parser(
        'devenv-matrix', help="Setup a matrix of environments.")
    SetupParam.add_parser_args(
        parser_devmat,
        include=['env_method'],
        env_method_default='mamba',
        skip=['for_development', 'deps_method', 'user',
              'method', 'python', 'env_name'],
        additional_args=[
            (('--method', '--methods'),
             {'nargs': '+', 'default': ['mamba', 'pip'],
              'choices': ['conda', 'pip', 'mamba'],
              'help': ("Method(s) that should be used to "
                       "install dependencies in the environments.")}),
            (('--python', '--pythons', '--version', '--versions'),
             {'nargs': '+', 'default': ['3.7'],
              'help': "Python version(s) for environments."}),
        ])
    # Build package
    parser_bld = subparsers.add_parser(
        'build', help="Build the package.")
    SetupParam.add_parser_args(parser_bld,
                               skip=['target_os', 'env_name'],
                               skip_types=['install'])
    # Install dependencies
    parser_dep = subparsers.add_parser(
        'deps', help="Install the package dependencies.")
    SetupParam.add_parser_args(parser_dep, skip=['python'],
                               deps_method_default="supplemental")
    # Install package
    parser_pkg = subparsers.add_parser(
        'install', help="Install the package.")
    SetupParam.add_parser_args(
        parser_pkg,
        deps_method_default="supplemental",
        method_choices=['conda', 'pip', 'mamba',
                        'conda-dev', 'pip-dev', 'mamba-dev'],
        method_help="Method that should be used to install yggdrasil.",
        additional_args=[
            (('--without-build', ),
             {'action': 'store_true',
              'help': ("Perform installation steps without building "
                       "first (assuming the package was already "
                       "built).")}),
            (('--without-deps', ),
             {'action': 'store_true',
              'help': ("Perform installation steps without installing "
                       "dependencies first (assuming the depdnencies "
                       "were already installed).")}),
        ])
    # Installation verification
    parser_ver = subparsers.add_parser(
        'verify', help="Verify that the package was installed correctly.")
    SetupParam.add_parser_args(parser_ver, skip_all=True,
                               install_opts=install_opts)
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
    # Call methods
    args = parser.parse_args()
    if args.operation in ['env', 'setup']:
        param = SetupParam.from_args(args, install_opts,
                                     env_created=True)
        create_env(args.env_method, args.python, param=param)
    elif args.operation == 'devenv':
        args.for_development = True
        args.deps_method = 'env'
        param = SetupParam.from_args(args, install_opts,
                                     env_created=True)
        create_env(args.env_method, args.python, param=param,
                   populate=True)
    elif args.operation == 'devenv-matrix':
        args.for_development = True
        args.deps_method = 'env'
        methods = args.method
        pythons = args.python
        for method in methods:
            for python in pythons:
                args.method = method
                args.python = python
                args.env_name = None
                param = SetupParam.from_args(args, install_opts,
                                             env_created=True)
                create_env(args.env_method, args.python, param=param,
                           populate=True)
    elif args.operation == 'build':
        param = SetupParam.from_args(args, install_opts)
        build_pkg(args.method, param=param)
    elif args.operation == 'deps':
        param = SetupParam.from_args(args, install_opts)
        install_deps(args.method, param=param, do_preinstall=True)
    elif args.operation == 'install':
        param = SetupParam.from_args(args, install_opts)
        install_pkg(args.method, param=param, python=args.python,
                    without_build=args.without_build,
                    without_deps=args.without_deps)
    elif args.operation == 'verify':
        param = SetupParam.from_args(args, install_opts)
        verify_pkg(install_opts=param.install_opts)
    elif args.operation == 'log':
        log_environment(new_filename=args.new_filename,
                        old_filename=args.old_filename)
