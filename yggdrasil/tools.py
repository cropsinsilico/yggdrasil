"""This modules offers various tools."""
from __future__ import print_function
import threading
import logging
import pprint
import os
import re
import sys
import glob
import sysconfig
try:
    from distutils import sysconfig as distutils_sysconfig
except ImportError:  # pragma: debug
    distutils_sysconfig = None
import warnings
import copy
import shutil
import inspect
import time
import signal
import uuid as uuid_gen
import subprocess
import importlib
import difflib
import contextlib
from yggdrasil import platform, constants
from yggdrasil.components import import_component, ComponentBase


class InvalidDefault:
    pass


logger = logging.getLogger(__name__)


_stack_in_log = False
_stack_in_timeout = False
if ((logging.getLogger("yggdrasil").getEffectiveLevel()
     <= logging.DEBUG)):  # pragma: debug
    _stack_in_log = False
    _stack_in_timeout = True
_environ_cache = []


def apply_recurse(x, func, **kwargs):
    r"""Apply a function recursively to all elements of x if it is
    a list, tuple, or dictionary.

    Args:
        x (list, tuple, dict): Object to apply function to.
        func (function): Function to apply to elements of x.
        **kwargs: Additional keyword arguments are passed to each
            function call.

    Returns:
        object: Version of input, but after applying func.

    """
    if isinstance(x, (list, tuple)):
        out = [func(ix, **kwargs) for ix in x]
        if isinstance(x, tuple):
            out = tuple(out)
    elif isinstance(x, dict):
        out = {k: func(v, **kwargs) for k, v in x.items()}
    else:  # pragma: debug
        raise TypeError("Recursion not supported for type '%s'"
                        % type(x))
    return out


def safe_decode(x):
    r"""Decode bytes, allowing for possiblity of invalid bytes.

    Args:
        x (bytes): Bytes to decode.

    Returns:
        str: Decoded string version of x.
    
    """
    if isinstance(x, str):
        return x
    try:
        return x.decode("utf-8") if x else ''
    except UnicodeDecodeError:
        return str(x)


def bytes2str(x, recurse=False):
    r"""Convert bytes type to string type.

    Args:
        x (bytes): String.
        recurse (bool, optional): If True and x is a list, tuple, or
            dict, the coversion will recurse. Defaults to False.

    Returns:
        str: Decoded string version of x.

    """
    if isinstance(x, bytes):
        out = x.decode("utf-8")
    elif isinstance(x, str):
        out = str(x)
    elif isinstance(x, (list, tuple, dict)) and recurse:
        out = apply_recurse(x, bytes2str, recurse=True)
    else:  # pragma: debug
        raise TypeError("Cannot convert type '%s' to str." % type(x))
    return out


def str2bytes(x, recurse=False):
    r"""Convert string type to bytes type.

    Args:
        x (str): String.
        recurse (bool, optional): If True and x is a list, tuple, or
            dict, the coversion will recurse. Defaults to False.

    Returns:
        bytes: Encoded bytes version of x.

    """
    if isinstance(x, str):
        out = x.encode("utf-8")
    elif isinstance(x, bytes):
        out = bytes(x)
    elif isinstance(x, (list, tuple, dict)) and recurse:
        out = apply_recurse(x, str2bytes, recurse=True)
    else:  # pragma: debug
        raise TypeError("Cannot convert type '%s' to bytes." % type(x))
    return out


def add_line_numbers(lines, for_diff=False):
    r"""Add number to lines.

    Args:
        lines (list): Lines to number.
        for_diff (bool, optional): If True, those lines beginning with
            removed/notation diff characters (-, ?) will not be numbered.
            Defaults to False.

    Returns:
        list: Numbered lines.

    """
    out = []
    i = 0
    for line in lines:
        if for_diff and line.startswith(('-', '?')):
            out.append('    ' + line)
        else:
            i += 1
            out.append('%2d: %s' % (i, line))
    return out


@contextlib.contextmanager
def timer_context(msg_format, **kwargs):
    r"""Context that will time commands executed within it and log a message.

    Args:
        msg_format (str): Format string used to format the elapsed time. It
            should include, at minimum, a '{elapsed}' field. Additional fields
            may also be present and can be fulfilled by additional keywords.
        **kwargs: Additional keyword arguments are passed to the format method
            on msg_format to create the log message.

    """
    start = time.time()
    try:
        yield
    finally:
        end = time.time()
        elapsed = end - start
        logger.info(msg_format.format(elapsed=elapsed, **kwargs))


def is_git_repository(path):
    r"""Check if a directory contains a git repository.

    Args:
        path (str): Directory to check.

    Returns:
        bool: True if path exists and is a git repository, False otherwise

    """
    import git
    if not os.path.isdir(path):
        return False
    try:
        git.Repo(path)
    except git.exc.InvalidGitRepositoryError:
        return False
    return True


def update_path_env(env_var, paths_to_add, env=None, add_to_front=False,
                    src_env=None):
    r"""Add a set of paths to an environment variable.

    Args:
        env_var (str): Environment variable to update
        paths_to_add (list): Paths to add if not present.
        env (dict, optional): Dictionary of environment variables to
            update if not provided, os.environ will be used.
        add_to_front (bool, optional): If True, added paths should be
            added before any existing paths.
        src_env (dict, optional): Environment variable set that existing
            paths should be pulled from if different from env.

    """
    if env is None:
        env = os.environ
    if src_env is None:
        src_env = env
    path_list = []
    prev_path = src_env.get(env_var, '')
    prev_path_list = []
    if prev_path:
        prev_path_list += prev_path.split(os.pathsep)
        path_list.append(prev_path)
    for x in paths_to_add:
        if x and x not in prev_path_list:
            if add_to_front:
                path_list.insert(0, x)
            else:
                path_list.append(x)
    if path_list:
        env[env_var] = os.pathsep.join(path_list)


def display_source(fname, number_lines=False, return_lines=False):
    r"""Display source code with syntax highlighting (if available).

    Args:
        fname (str, list): Full path(s) to one or more source files.
        number_lines (bool, optional): If True, line numbers will be added
            to the displayed examples. Defaults to False.
        return_lines (bool, optional): If True, the lines are returned rather
            than displayed. Defaults to False.

    """
    if isinstance(fname, list):
        out = ''
        for f in fname:
            iout = display_source(f, number_lines=number_lines,
                                  return_lines=return_lines)
            if return_lines:
                out += iout
        if return_lines:
            return out
        return
    if isinstance(fname, (bytes, str)):
        with open(fname, 'r') as fd:
            lines = fd.read()
        try:
            language = constants.EXT2LANG[os.path.splitext(fname)[-1]]
        except KeyError:
            language = None
        prefix = 'file: %s' % fname
    else:
        lines = inspect.getsource(fname)
        language = 'python'
        prefix = '%s: %s' % (type(fname), fname)
    try:
        from pygments import highlight
        from pygments.lexers import PythonLexer
        from pygments.lexers.data import YamlLexer
        from pygments.lexers.c_cpp import CLexer, CppLexer
        from pygments.lexers.r import SLexer
        from pygments.lexers.fortran import FortranLexer
        from pygments.lexers.matlab import MatlabLexer
        from pygments.lexers.html import XmlLexer
        from pygments.formatters import Terminal256Formatter
        lexer_map = {'python': PythonLexer,
                     'yaml': YamlLexer,
                     'c': CLexer,
                     'cxx': CppLexer,
                     'c++': CppLexer,
                     'r': SLexer,
                     'fortran': FortranLexer,
                     'matlab': MatlabLexer,
                     'xml': XmlLexer}
        lines = highlight(lines, lexer_map[language](),
                          Terminal256Formatter())
    except (ImportError, KeyError):
        pass
    if number_lines:
        lines = '\n'.join(add_line_numbers(lines.splitlines()))
    if return_lines:
        return lines
    lines = '%s\n%s\n%s\n' % (prefix, len(prefix) * '=', lines)
    print(lines)


def ndiff(a, b, ncontext=-1, number_lines=False, **kwargs):
    r"""Get the diff between two lists of strings.

    Args:
        a (list): List of strings.
        b (list): List of strings.
        ncontext (int, optional): Number of lines before and after
             differences that should be kept for context. If -1, all lines
             will be included.
        number_lines (bool, optional): If True, line numbers will be added
            to the diff. Defaults to False.
        **kwargs: Additional keyword arguments are passed to difflib.ndiff.

    Returns:
        list: List of line differences.

    """
    diff = list(difflib.ndiff(a, b, **kwargs))
    selected = []
    if ncontext == -1:
        selected = slice(0, len(diff))
    else:
        i = 0
        last_end = 0
        start = -1
        end = -1
        for i, x in enumerate(diff):
            if x.startswith(('-', '+', '?')):
                if start == -1:
                    start = max(last_end, i - ncontext)
                end = min(len(diff), i + ncontext + 1)
            else:
                selected.append(slice(start, end))
                last_end = end
                start = -1
                end = -1
        if start != -1:
            selected.append(slice(start, end))
    if number_lines:
        diff = add_line_numbers(diff, for_diff=True)
    out = []
    for i, x in enumerate(selected):
        if i > 0 and x.start != selected[i - 1].stop:
            out += [' ...']
        out += diff[x]
    return out


def display_source_diff(fname1, fname2, return_lines=False, **kwargs):
    r"""Display a diff between two source code files with syntax highlighting
    (if available).

    Args:
        fname1 (str): Name of first source file.
        fname2 (src): Name of second source file.
        return_lines (bool, optional): If True, the lines are returned rather
            than displayed. Defaults to False.
        **kwargs: Additional keyword arguments are passed to ndiff.

    """
    src1 = display_source(fname1, return_lines=True)
    src2 = display_source(fname2, return_lines=True)
    diff = ndiff(src1.splitlines(), src2.splitlines(), **kwargs)
    if isinstance(fname1, str):
        prefix_type1 = 'file'
    else:
        prefix_type1 = str(type(fname1))
    if isinstance(fname2, str):
        prefix_type2 = 'file'
    else:
        prefix_type2 = str(type(fname2))
    prefix1 = '%s1: %s' % (prefix_type1, fname1)
    prefix2 = '%s2: %s' % (prefix_type2, fname2)
    lines = '%s\n%s\n%s\n%s\n' % (prefix1, prefix2,
                                  max(len(prefix1), len(prefix2)) * '=',
                                  '\n'.join(diff))
    if return_lines:
        return lines
    print(lines)


def dict_diff(a, b):
    r"""Get the parameters that differ between two dictionaries.

    Args:
        a (dict): First dictionary for comparison.
        b (dict): Second dictionary for comparison.

    Returns:
        dict: Key/value pairs from a that differ from those in b.

    """
    return {k: v for k, v in a.items() if v != b.get(k, None)}
    

def get_fds(by_column=None, ignore_closed=False, ignore_kqueue=False,
            ignore_cwd=False, ignore_types=None, verbose=False):  # pragma: debug
    r"""Get a list of open file descriptors."""
    out = subprocess.check_output(
        'lsof -p {} | grep -v txt'.format(os.getpid()), shell=True)
    if verbose:
        print(f'{len(out.splitlines()) - 1}\n' + out.decode('utf8'))
    out = out.splitlines()[1:]
    if ignore_closed:
        out = [x for x in out if not x.endswith(b'(CLOSED)')]
    if ignore_kqueue:
        out = [x for x in out if not x.endswith(b'state=0xa')]
    if ignore_cwd:
        out = [x for x in out if x.split()[3] != b'cwd']
    if ignore_types:
        out = [x for x in out
               if x.split()[4].decode('utf8') not in ignore_types]
    if by_column is not None:
        return {x.split()[by_column]: x for x in out}
    return out


@contextlib.contextmanager
def track_fds(prefix='', **kwargs):  # pragma: debug
    kwargs['by_column'] = 3
    fds0 = get_fds(**kwargs)
    yield
    fds1 = get_fds(**kwargs)
    new_fds = set(fds1.keys()) - set(fds0.keys())
    diff = [fds1[k] for k in sorted(new_fds)]
    if diff:
        print(f'{prefix}{len(diff)} fds\n\t' + '\n\t'.join(
            [x.decode('utf8') for x in diff]))
    

def get_shell():
    r"""Get the type of shell that yggdrasil was called from.

    Returns:
        str: Name of the shell.

    """
    shell = os.environ.get('SHELL', None)
    if not shell:
        if platform._is_win:  # pragma: windows
            shell = os.environ.get('COMSPEC', None)
        else:
            shell = '/bin/sh'  # Default used by subprocess
        assert shell
    # return psutil.Process(os.getppid()).name()
    if platform._is_win:  # pragma: windows
        shell = shell.lower()
    return shell


def in_powershell():
    r"""Determine if yggdrasil is running from a Windows Powershell.

    Returns:
        bool: True if running from Powershell, False otherwise.

    """
    if not platform._is_win:
        return False
    shell = get_shell()
    return bool(re.match('pwsh|pwsh.exe|powershell.exe', shell))


def check_environ_bool(name, valid_values=['true', '1', True, 1]):
    r"""Check to see if a boolean environment variable is set to True.

    Args:
        name (str): Name of environment variable to check.
        valid_values (list, optional): Values for the environment variable
            that indicate it is True. These should all be lower case as
            the lower case version of the variable contents will be compared
            to the list. Defaults to ['true', '1'].

    Returns:
        bool: True if the environment variables is set and is one of the
            list valid_values (after being transformed to lower case).

    """
    return (os.environ.get(name, '').lower() in valid_values)


def update_environ(env, exclusive=False):
    r"""Update the current environment variables.

    Args:
        env (dict): Environment variables to update.
        exclusive (bool, optional): If True, only those variables in
            env will be present after the update. If False, the
            variables in env will be updated via the 'update' method and
            any existing variables not specified in env will remain.

    """
    if env is None:
        return
    os.environ.update(env)
    if exclusive:
        for k in list(os.environ.keys()):
            if k not in env:
                del os.environ[k]


def cache_environ():
    r"""Cache the current environment variables."""
    global _environ_cache
    _environ_cache.append(copy.deepcopy(os.environ))


def restored_cached_environ():
    r"""Restore the last set of cached environment variables."""
    global _environ_cache
    oldenv = _environ_cache.pop()
    update_environ(oldenv, exclusive=True)


@contextlib.contextmanager
def updated_environment(env, exclusive=False):
    r"""Context to perform actions with an updated set of environment
    variables.

    Args:
        env (dict): Environment variables to add within the context.
        exclusive (bool, optional): If True, only those variables in
            env will be present within the context. If False, the
            variables in env will be updated via the 'update' method and
            any existing variables not specified in env will remain.

    """
    cache_environ()
    update_environ(env, exclusive=exclusive)
    yield
    restored_cached_environ


def get_numpy_c_library(allow_failure=False, libtype=None):
    r"""Determine the location of the Numpy C API library.
    assert libtype in ['include']

    Args:
        allow_failure (bool, optional): If True, the base name will be
            returned if the file cannot be located. Defaults to False.
        libtype (str, optional): Type of library that should be located.
            Valid values include 'include'. Defaults to 'include'.

    Returns:
        str: Full path to the library.

    Raises:
        ValueError: If libtype is not 'include'

    """
    import numpy as np
    if libtype not in ['include']:  # pragma: debug
        raise ValueError(f"libtype must be 'include', "
                         f"'{libtype}' not supported.")
    np_dir = None
    try:
        np_dir = np.get_include()
    except AttributeError:  # pragma: debug
        from numpy import distutils as numpy_distutils
        np_dir = numpy_distutils.misc_util.get_numpy_include_dirs()[0]
    return os.path.join(np_dir, 'numpy', 'arrayobject.h')


def get_python_c_library(allow_failure=False, libtype=None):
    r"""Determine the location of the Python C API library.

    Args:
        allow_failure (bool, optional): If True, the base name will be returned
            if the file cannot be located. Defaults to False.
        libtype (str, optional): Type of library that should be located.
            Valid values include 'static' and 'shared'. Defaults to 'shared'
            on Unix OSs and 'static' on Windows.

    Returns:
        str: Full path to the library.

    Raises:
        ValueError: If libtype is not 'static' or 'shared'.
        RuntimeError: If the base name for the library cannot be determined.
        RuntimeError: If the library cannot be located.

    """
    if libtype not in ['static', 'shared', 'windows_import',
                       'include', None]:  # pragma: debug
        raise ValueError("libtype must be 'shared' or 'static', "
                         "'%s' not supported." % libtype)
    paths = sysconfig.get_paths()
    cvars = sysconfig.get_config_vars()
    if libtype is None:
        libtype = 'shared'
    if libtype == 'include':
        return os.path.join(paths['include'], 'Python.h')
    if platform._is_win:  # pragma: windows
        libtype2ext = {'shared': '.dll',
                       'static': '.lib',
                       'windows_import': '.lib'}
        prefix = ''
        base = '%spython%s%s' % (prefix,
                                 cvars['py_version_nodot'],
                                 libtype2ext[libtype])
    elif sys.version_info[:2] < (3, 8):
        libtype2key = {'shared': 'LDLIBRARY', 'static': 'LIBRARY'}
        base = cvars.get(libtype2key[libtype], None)
    else:
        if platform._is_mac:
            libtype2ext = {'shared': '.dylib', 'static': '.a'}
        else:
            libtype2ext = {'shared': '.so', 'static': '.a'}
        prefix = 'lib'
        base = '%spython%s%s' % (prefix,
                                 cvars['py_version_short'],
                                 libtype2ext[libtype])
    if platform._is_mac and base.endswith('/Python'):  # pragma: no cover
        base = 'libpython%s.dylib' % cvars['py_version_short']
    if base is None:  # pragma: debug
        raise RuntimeError(("Could not determine base name for the Python "
                            "C API library.\n"
                            "sysconfig.get_paths():\n%s\n"
                            "sysconfig.get_config_vars():\n%s\n")
                           % (pprint.pformat(paths),
                              pprint.pformat(cvars)))
    dir_try = []
    for x in [get_conda_prefix(), cvars['prefix']]:
        if x:
            dir_try.append(x)
            if platform._is_win:  # pragma: windows
                dir_try.append(os.path.join(x, 'libs'))
            else:
                dir_try.append(os.path.join(x, 'lib'))
    for k in ["LIBPL", "LIBDIR", "LIBDEST", "Prefix", "ExecPrefix",
              "BaseExecPrefix"]:
        if cvars.get(k, None) and (cvars[k] not in dir_try):
            dir_try.append(cvars[k])
    for k in ['stdlib', 'purelib', 'platlib', 'platstdlib', 'data']:
        if paths.get(k, None) and (paths[k] not in dir_try):
            dir_try.append(paths[k])
    dir_try.append(os.path.join(paths['data'], 'lib'))
    if distutils_sysconfig is not None:
        dir_try.append(os.path.dirname(
            distutils_sysconfig.get_python_lib(True, True)))
    dir_try = set(dir_try)
    for idir in dir_try:
        x = os.path.join(idir, base)
        if os.path.isfile(x):
            return x
    error = (f"Could not determine the location of the Python "
             f"C API library: {base}.\n"
             f"sysconfig.get_paths():\n{pprint.pformat(paths)}\n"
             f"sysconfig.get_config_vars():\n{pprint.pformat(cvars)}\n"
             f"tried:\n{pprint.pformat(dir_try)}")  # pragma: debug
    if allow_failure:  # pragma: debug
        warnings.warn(error)
        return base
    raise RuntimeError(error)  # pragma: debug


def get_env_prefixes():
    r"""Determine the environment path prefix (virtualenv or conda) for
    the current environment.

    Returns:
        list: Full path to the directory prefixes used for the current
            environments if one (or more) exists. If neither a
            virtualenv or conda prefix can be located, None is returned.

    Raises:
        RuntimeError: If both virtualenv and conda environments are
            located.

    """
    out = []
    venv = get_venv_prefix()
    cenv = get_conda_prefix()
    if venv:
        out.append(venv)
    if cenv:
        out.append(cenv)
    return out


def get_venv_prefix():
    r"""Determine the virtualenv path prefix for the current environment.

    Returns:
        str: Full path to the directory prefix used for the current
            virtualenv environment if one exists. If virtualenv cannot
            be located, None is returned.

    """
    return os.environ.get('VIRTUAL_ENV', None)


def get_conda_prefix(env=None):
    r"""Determine the conda path prefix for the current environment.

    Args:
        env (str, optional): Environment to get the prefix for. If not
            provided, the current environment's prefix will be returned.

    Returns:
        str: Full path to the directory prefix used for the current conda
            environment if one exists. If conda cannot be located, None is
            returned.

    """
    if env:
        conda_root = get_conda_root()
        if conda_root is None:
            return None
        return os.path.join(conda_root, 'envs', env)
    conda_prefix = os.environ.get('CONDA_PREFIX', None)
    # This part should be enabled if the conda base enviroment dosn't have
    # CONDA_PREFIX set. Older version of conda behaved this way so it is
    # possible that a future release will as well.
    # if not conda_prefix:
    #     conda_prefix = shutil.which('conda')
    #     if conda_prefix is not None:
    #         conda_prefix = os.path.dirname(os.path.dirname(conda_prefix))
    return conda_prefix


def get_conda_env():
    r"""Determine the name of the current conda environment.

    Returns:
        str: Name of the current conda environment if one is activated. If a
            conda environment is not activated, None is returned.

    """
    return os.environ.get('CONDA_DEFAULT_ENV', None)


def get_conda_root():
    r"""Get the root directory containing all conda environments if one
    exists.

    Returns:
        str: Root directory containing conda environments. If conda is
            not installed, None is returned.

    """
    conda_prefix = get_conda_prefix()
    if conda_prefix is None:
        return None
    conda_env = get_conda_env()
    if conda_prefix.endswith(conda_env):
        return os.path.dirname(os.path.dirname(conda_prefix))
    return conda_prefix


def call_conda_command(command, env=None, args=None, return_output=False,
                       default_to_mamba=False, return_command=False,
                       **kwargs):
    r"""Call a conda command.

    Args:
        command (str): Conda command.
        env (str, optional): Environment to call the command for.
        args (list, optional): Additional arguments to pass to the
            command.
        return_output (bool, optional): If True, the output from the
            command will be returned.
        default_to_mamba (bool, optional): If True, mamba will be used in
            place of conda if it is installed.
        return_command (bool, optional): If True, the command will be
            returned.
        **kwargs: Additional keyword arguments are passed to
            subprocess.check_call or subprocess.check_output.

    """
    if default_to_mamba and shutil.which('mamba'):
        executable = 'mamba'
    else:
        executable = 'conda'
    cmd = [executable, command]
    if env:
        cmd += ['-n', env]
    if args:
        cmd += args
    if platform._is_win:  # pragma: windows
        # Conda/mamba commands must be run on the shell on
        # windows as it is implemented as a batch script
        cmd.insert(0, 'call')
        kwargs['shell'] = True
    if kwargs.get('shell', False):
        cmd = ' '.join(cmd)
    if return_command:
        return cmd
    if return_output:
        return subprocess.check_output(cmd, **kwargs)
    return subprocess.check_call(cmd, **kwargs)


def get_subprocess_language():
    r"""Determine the language of the calling process.

    Returns:
        str: Name of the programming language responsible for the subprocess.

    """
    return os.environ.get('YGG_MODEL_LANGUAGE', 'python')


def get_subprocess_language_driver():
    r"""Determine the driver for the langauge of the calling process.

    Returns:
        ModelDriver: Class used to handle running a model of the process language.

    """
    return import_component('model', get_subprocess_language())


def is_subprocess():
    r"""Determine if the current process is a subprocess.

    Returns:
        bool: True if YGG_SUBPROCESS environment variable is True, False
            otherwise.

    """
    return check_environ_bool('YGG_SUBPROCESS')


def escape_regex(name):
    r"""Escape special characters in name that would be interpreted as
    regexes.

    Args:
        name (str): String to escape.

    Returns:
        str: Escaped string.

    """
    out = name
    for k in '\\?-+*$%#@!^&(){}[]<>,.;:':
        out = out.replace(k, '\\' + k)
    return out


def convert_regex_to_find(name):
    r"""Convert a regex pattern for fortran to the format expected by the
    linux find command.

    Args:
        name (str): Pattern to convert.

    Returns:
        str: Converted pattern,

    """
    out = re.sub(r'(^|(?:[^\\]))\(', r'\1\(', name)
    out = re.sub(r'(^|(?:[^\\]))\)', r'\1\)', out)
    return out


def find_all(name, path, verification_func=None, use_regex=False,
             use_os=False):
    r"""Find all instances of a file with a given name within the directory
    tree starting at a given path.

    Args:
        name (str): Name of the file to be found (with the extension).
        path (str, None): Directory where search should start. If set to
            None on Windows, the current directory and PATH variable are
            searched.
        verification_func (function, optional): Function that returns
            True when a file is valid and should be returned and False
            otherwise. Defaults to None and is ignored.
        use_regex (bool, str, optional): If True or string, use full
            regex to interpret name and locate files. If a string is
            provided, it will be used as the regex pattern, otherwise
            name will be used. A string is required unless use_os is True
        use_os (bool, optional): If True, use a system tool to search
            for the file (find on unix, where on windows).

    Returns:
        list: All instances of the specified file.

    """
    result = []
    args = []
    regex_pattern = use_regex if isinstance(use_regex, str) else name
    regex_pattern = r'.*' + regex_pattern  # to match the directory
    if use_os:
        try:
            if platform._is_win:  # pragma: windows
                assert not use_regex
                args = ["where"]
                if path is None:
                    args += [name]
                    out = subprocess.check_output(
                        args, env=os.environ,
                        stderr=subprocess.STDOUT)
                else:
                    args += ["/r", path, name]
                    out = subprocess.check_output(
                        args, env=os.environ,
                        stderr=subprocess.STDOUT)
            else:
                shell = False
                args = ["find", "-L", path, "-type", "f"]
                if use_regex:
                    regex_pattern = convert_regex_to_find(regex_pattern)
                    args += ["-regex", regex_pattern]
                    args.insert(1, "-E")
                    args = ' '.join(args)
                    shell = True
                else:
                    args += ["-name", name]
                pfind = subprocess.Popen(
                    args, env=os.environ, shell=shell,
                    stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE)
                if isinstance(args, list):
                    args = ' '.join(args)
                (stdoutdata, stderrdata) = pfind.communicate()
                out = stdoutdata
                for line in stderrdata.splitlines():
                    if b'Permission denied' not in line:
                        raise subprocess.CalledProcessError(
                            pfind.returncode, args,
                            output=stderrdata)
        except subprocess.CalledProcessError as e:
            logger.info(f"Error in called process \'{args}\': {e}")
            out = ''
        if not out.isspace():
            result = sorted(out.splitlines())
    else:
        result = glob.glob(os.path.join(path, name))
        if use_regex:
            result = [
                x for x in result if re.fullmatch(regex_pattern, x)]
    result = sorted(
        [os.path.normcase(os.path.normpath(bytes2str(m)))
         for m in result])
    if verification_func is not None:
        result = [x for x in result if verification_func(x)]
    return result


def locate_file(fname, environment_variable='PATH', directory_list=None,
                show_alternates=False, select_return='first', **kwargs):
    r"""Locate a file within a set of paths defined by a list or environment
    variable.

    Args:
        fname (str, list): One or more possible names of the file that should be
            located. If a list is provided, the path for the first entry for
            which a match could be located will be returned and subsequent entries
            will not be checked.
        environment_variable (str): Environment variable containing the set of
            paths that should be searched. Defaults to 'PATH'. If None, this
            keyword argument will be ignored. If a list is provided, it is
            assumed to be a list of environment variables that should be
            searched in the specified order.
        directory_list (list): List of paths that should be searched in addition
            to those specified by environment_variable. Defaults to None and is
            ignored. These directories will be searched be for those in the
            specified environment variables.
        show_alternates (bool, optional): If True and there is more
            than one match, the alternate matches will be printed in
            a warning message. Defaults to False.
        select_return (str, optional): Method that should be used to select
            the returned value if there is more than one option.
              'first'   : Return the first value, alphabetically sorted.
              'last'    : Return the last value, alphabetically sorted.
              'longest' : Return the longest value.
              'shortest': Return the shortest value.
        **kwargs: Additional keyword arguments are passed to find_all.

    Returns:
        bool, str: Full path to the located file if it was located, False
            otherwise.

    """
    if isinstance(fname, list):
        out = False
        for ifname in fname:
            out = locate_file(ifname, environment_variable=environment_variable,
                              directory_list=directory_list,
                              show_alternates=show_alternates,
                              select_return=select_return, **kwargs)
            if out:
                break
        return out
    out = []
    if ((platform._is_win and (environment_variable == 'PATH')
         and (directory_list is None)
         and kwargs.get('use_os', False))):  # pragma: windows
        out += find_all(fname, None, **kwargs)
    else:
        if directory_list is None:
            directory_list = []
        if environment_variable is not None:
            if not isinstance(environment_variable, list):
                environment_variable = [environment_variable]
            for x in environment_variable:
                directory_list += os.environ.get(x, '').split(os.pathsep)
        for path in directory_list:
            if path:
                out += find_all(fname, path, **kwargs)
            if out and (not show_alternates):
                break
    if not out:
        return False
    if len(out) > 1:
        if select_return in ['first', 'last']:
            out = sorted(out)
        elif select_return in ['longest', 'shortest']:
            out = sorted(out, key=len)
        else:  # pragma: debug
            raise NotImplementedError(select_return)
        if select_return in ['last', 'longest']:
            out = out[::-1]
    first = out[0]
    if show_alternates:  # pragma: debug
        out = set(out)
        out.remove(first)
        if len(out) > 0:
            warnings.warn(
                f"More than one ({len(out) + 1}) match to {fname}:\n"
                f"{pprint.pformat(out)}\n "
                f"Using {select_return} match ({first})", RuntimeWarning)
    return first


def locate_path(fname, basedir=os.path.abspath(os.sep)):
    r"""Find the full path to a file using where on Windows."""
    try:
        if platform._is_win:  # pragma: windows
            out = subprocess.check_output(["dir", fname, "/s/b"], shell=True,
                                          cwd=basedir)
            # out = subprocess.check_output(["where", fname])
        else:
            # find . -name "filetofind" 2>&1 | grep -v 'permission denied'
            out = subprocess.check_output(["find", basedir, "-name", fname])  # ,
            # "2>&1", "|", "grep", "-v", "'permission denied'"])
            # out = subprocess.check_output(["locate", "-b", "--regex",
            #                                "^%s" % fname])
    except subprocess.CalledProcessError:  # pragma: debug
        return False
    if out.isspace():  # pragma: debug
        return False
    out = bytes2str(out).splitlines()
    return out


def remove_path(fpath, timeout=60.0):
    r"""Delete a single file.

    Args:
        fpath (str): Full path to a file or directory that should be
            removed.
        timeout (float, optional): Time (in seconds) that should be
            waited before raising an error that a file cannot be removed.
            Defaults to 60.0.

    Raises:
        RuntimeError: If the product cannot be removed.

    """
    from yggdrasil import multitasking
    if os.path.isdir(fpath):
        ftype = 'directory'
        fcheck = os.path.isdir
        fremove = shutil.rmtree
    elif os.path.isfile(fpath):
        ftype = 'file'
        fcheck = os.path.isfile
        fremove = os.remove
    else:
        return
    errors = []
    # if platform._is_win and (ftype == 'directory'):  # pragma: windows
    #     fremove_base = fremove

    #     def fremove(path):
    #         try:
    #             fremove_base(path)
    #         except PermissionError:
    #             # https://stackoverflow.com/questions/2656322/shutil-rmtree-
    #             # fails-on-windows-with-access-is-denied
    #             import stat
    #             if not os.access(path, os.W_OK):
    #                 # Is the error an access error ?
    #                 os.chmod(path, stat.S_IWUSR)
    #                 fremove_base(path)
    #             else:  # pragma: debug
    #                 raise
    
    def is_removed():
        if fcheck(fpath):
            try:
                fremove(fpath)
            except BaseException as e:  # pragma: debug
                errors.append(e)
        return (not fcheck(fpath))
    try:
        multitasking.wait_on_function(is_removed, timeout=timeout)
    except multitasking.TimeoutError as e:  # pragma: debug
        if errors:
            raise errors[-1]
        if not e.function_value:
            raise multitasking.TimeoutError(
                "Failed to remove %s: %s" % (ftype, fpath))


def get_supported_platforms():
    r"""Get a list of the platforms supported by yggdrasil.

    Returns:
        list: The name of platforms supported by yggdrasil.

    """
    return copy.deepcopy(platform._supported_platforms)


def resolve_language_aliases(language):
    r"""Get a list of languages, replacing any aliases.

    Args:
        language (str, list): One or more language.

    Returns:
        str, list: Aliased language(s).

    """
    if isinstance(language, (list, tuple)):
        return [resolve_language_aliases(x) for x in language]
    for k, v in constants.ALIASED_LANGUAGES.items():
        if language in v:
            return k
    return language


def is_language_alias(x, language):
    r"""Check if a string is an alias for a language.

    Args:
        x (str): String to check.
        language (str, list): One or more language to check aliases of.

    Returns:
        str, bool: Returns the version of the language in the provided set if
            x is an alias and False otherwise.

    """
    if isinstance(language, str):
        language = [language]
    for xx in [x, x.lower(), x.upper()]:
        if xx in language:
            return xx
    aliases = []
    for k, v in constants.ALIASED_LANGUAGES.items():
        if x in v:
            aliases = v
    for v in aliases:
        if v in language:
            return v
    return False


def get_supported_lang():
    r"""Get a list of the model programming languages that are supported
    by yggdrasil.

    Returns:
        list: The names of programming languages supported by yggdrasil.
    
    """
    out = constants.LANGUAGES['all'].copy()
    if 'c++' in out:
        out[out.index('c++')] = 'cpp'
    return list(set(out))


def get_supported_type():
    r"""Get a list of the data types that are supported by yggdrasil.

    Returns:
        list: The names of data types supported by yggdrasil.

    """
    from yggdrasil import rapidjson
    return rapidjson.get_metaschema()['definitions']['simpleTypes']['enum']


def get_supported_comm(dont_include_value=False):
    r"""Get a list of the communication mechanisms supported by yggdrasil.

    Args:
        dont_include_value (bool, optional): If True, don't include the
            ValueComm in the list returned. Defaults to False.

    Returns:
        list: The names of communication mechanisms supported by yggdrasil.

    """
    from yggdrasil import constants
    excl_list = ['CommBase', 'DefaultComm', 'default']
    if dont_include_value:
        excl_list += ['ValueComm', 'value']
    out = list(constants.COMPONENT_REGISTRY['comm']['subtypes'].keys())
    for k in excl_list:
        if k in out:
            out.remove(k)
    return out  # list(set(out))


def is_lang_installed(lang):
    r"""Check to see if yggdrasil can run models written in a programming
    language on the current machine.

    Args:
        lang (str): Programming language to check.

    Returns:
        bool: True if models in the provided language can be run on the current
            machine, False otherwise.

    """
    drv = import_component('model', lang)
    return drv.is_installed()


def is_comm_installed(comm, language=None):
    r"""Check to see if yggdrasil can use a communication mechanism on the
    current machine.

    Args:
        comm (str): Communication mechanism to check.
        language (str, optional): Specific programming language that
            communication mechanism should be check for. Defaults to None and
            all supported languages will be checked.

    Returns:
        bool: True if the communication mechanism can be used on the current
            machine, False otherwise.

    """
    cmm = import_component('comm', comm)
    return cmm.is_installed(language=language)


def get_installed_lang():
    r"""Get a list of the languages that are supported by yggdrasil on the
    current machine. This checks for the necessary interpreters, licenses, and/or
    compilers.

    Returns:
        list: The name of languages supported on the current machine.
    
    """
    out = []
    all_lang = get_supported_lang()
    for k in all_lang:
        if is_lang_installed(k):
            out.append(k)
    return out


def get_installed_comm(language=None, dont_include_value=False):
    r"""Get a list of the communication channel types that are supported by
    yggdrasil on the current machine. This checks the operating system,
    supporting libraries, and broker credentials. The order indicates the
    prefered order of use.

    Args:
        language (str, optional): Specific programming language that installed
            comms should be located for. Defaults to None and all languages
            supported on the current platform will be checked.
        dont_include_value (bool, optional): If True, don't include the
            ValueComm in the list returned. Defaults to False.


    Returns:
        list: The names of the the communication channel types supported on
            the current machine.

    """
    out = []
    all_comm = get_supported_comm(dont_include_value=dont_include_value)
    for k in all_comm:
        if is_comm_installed(k, language=language):
            out.append(k)
    # Fix order to denote preference
    out_sorted = []
    for k in ['zmq', 'ipc', 'rmq']:
        if k in out:
            out.remove(k)
            out_sorted.append(k)
    out_sorted += out
    return out_sorted


def get_default_comm():
    r"""Get the default comm that should be used for message passing."""
    if 'YGG_DEFAULT_COMM' in os.environ:
        _default_comm = os.environ['YGG_DEFAULT_COMM']
        # if not is_comm_installed(_default_comm, language='any'):  # pragma: debug
        #     raise Exception('Unsupported default comm %s set by YGG_DEFAULT_COMM' % (
        #                     _default_comm))
    else:
        comm_list = get_installed_comm()
        if len(comm_list) > 0:
            _default_comm = comm_list[0]
        else:  # pragma: windows
            # Locate comm that maximizes languages that can be run
            tally = {}
            for c in get_supported_comm(dont_include_value=True):
                tally[c] = 0
                for lang in get_supported_lang():
                    if is_comm_installed(c, language=lang):
                        tally[c] += 1
            _default_comm = max(tally)
            if tally[_default_comm] == 0:  # pragma: debug
                raise Exception('Could not locate an installed comm.')
    if _default_comm.endswith('Comm'):  # pragma: debug
        _default_comm = import_component('comm', _default_comm)._commtype
    # if _default_comm == 'rmq':  # pragma: debug
    #     raise NotImplementedError('RMQ cannot be the default comm because '
    #                               + 'there is not an RMQ C interface.')
    return _default_comm


def get_YGG_MSG_MAX(comm_type=None):
    r"""Get the maximum message size for a given comm type.

    Args:
        comm_type (str, optional): The name of the communication type that the
            maximum message size should be returned for. Defaults to result of
            get_default_comm() if not provided.

    Returns:
        int: Maximum message size (in bytes).

    """
    if comm_type is None:
        comm_type = get_default_comm()
    if comm_type in ['ipc', 'IPCComm']:
        # OS X limit is 2kb
        out = 1024 * 2
    else:
        out = 2**20
    return out


# https://stackoverflow.com/questions/35772001/
# how-to-handle-the-signal-in-python-on-windows-machine
def kill(pid, signum):
    r"""Kill process by mapping signal number.

    Args:
        pid (int): Process ID.
        signum (int): Signal that should be sent.

    """
    if platform._is_win:  # pragma: debug
        sigmap = {signal.SIGINT: signal.CTRL_C_EVENT,
                  signal.SIGBREAK: signal.CTRL_BREAK_EVENT}
        if signum in sigmap and pid == os.getpid():
            # we don't know if the current process is a
            # process group leader, so just broadcast
            # to all processes attached to this console.
            pid = 0
        thread = threading.current_thread()
        handler = signal.getsignal(signum)
        # work around the synchronization problem when calling
        # kill from the main thread.
        if (((signum in sigmap) and (thread.name == 'MainThread')
             and callable(handler) and ((pid == os.getpid()) or (pid == 0)))):
            event = threading.Event()

            def handler_set_event(signum, frame):
                event.set()
                return handler(signum, frame)

            signal.signal(signum, handler_set_event)
            try:
                os.kill(pid, sigmap[signum])
                # busy wait because we can't block in the main
                # thread, else the signal handler can't execute.
                while not event.is_set():
                    pass
            finally:
                signal.signal(signum, handler)
        else:
            os.kill(pid, sigmap.get(signum, signum))
    else:
        os.kill(pid, signum)


def sleep(interval):
    r"""Sleep for a specified number of seconds.

    Args:
        interval (float): Time in seconds that process should sleep.

    """
    time.sleep(interval)


def safe_eval(statement, **kwargs):
    r"""Run eval with a limited set of builtins and Python libraries/functions.

    Args:
        statement (str): Statement that should be evaluated.
        **kwargs: Additional keyword arguments are variables that are made available
            to the statement during evaluation.

    Returns:
        object: Result of the eval.

    """
    safe_dict = {}
    _safe_lists = {
        'math': [
            'acos', 'asin', 'atan', 'atan2', 'ceil', 'cos',
            'cosh', 'degrees', 'e', 'exp', 'fabs', 'floor', 'fmod',
            'frexp', 'hypot', 'ldexp', 'log', 'log10', 'modf', 'pi',
            'pow', 'radians', 'sin', 'sinh', 'sqrt', 'tan', 'tanh'],
        'builtins': [
            'abs', 'any', 'bool', 'bytes', 'float', 'int', 'len',
            'list', 'map', 'max', 'min', 'repr', 'set', 'str',
            'sum', 'tuple', 'type', 'isinstance'],
        'numpy': [
            'array', 'int8', 'int16', 'int32', 'int64',
            'uint8', 'uint16', 'uint32', 'uint64',
            'float16', 'float32', 'float64'],
        'pandas': [
            'DataFrame'],
        'yggdrasil.units': [
            'get_data', 'add_units', 'Quantity', 'QuantityArray']}
    for mod_name, func_list in _safe_lists.items():
        mod = importlib.import_module(mod_name)
        for func in func_list:
            safe_dict[func] = getattr(mod, func)
    safe_dict.update(kwargs)
    # The following replaces <Class Name(a, b)> style reprs with calls to classes
    # identified in self._no_eval_class
    # regex = r'<([^<>]+)\(([^\(\)]+)\)>'
    # while True:
    #     match = re.search(regex, statement)
    #     if not match:
    #         break
    #     cls_repl = self._no_eval_class.get(match.group(1), False)
    #     if not cls_repl:
    #         raise ValueError("Expression '%s' in '%s' is not eval friendly."
    #                          % (match.group(0), statement))
    #     statement = statement.replace(match.group(0),
    #                                   '%s(%s)' % (cls_repl, match.group(2)), 1)
    return eval(statement, {"__builtins__": None}, safe_dict)


def eval_kwarg(x):
    r"""If x is a string, eval it. Otherwise just return it.

    Args:
        x (str, obj): String to be evaluated as an object or an object.

    Returns:
        obj: Result of evaluated string or the input object.

    """
    if isinstance(x, str):
        try:
            return eval(x)
        except NameError:
            return x
    return x


class ProxyMeta(type):
    r"""Metaclass for handling proxy."""

    _special_names = [
        '__abs__', '__add__', '__and__', '__call__', '__cmp__', '__coerce__',
        '__contains__', '__delitem__', '__delslice__', '__div__', '__divmod__',
        '__eq__', '__float__', '__floordiv__', '__ge__', '__getitem__',
        '__getslice__', '__gt__', '__hex__', '__iadd__', '__iand__',
        '__idiv__', '__idivmod__', '__ifloordiv__', '__ilshift__', '__imod__',
        '__imul__', '__int__', '__invert__', '__ior__', '__ipow__', '__irshift__',
        '__isub__', '__iter__', '__itruediv__', '__ixor__', '__le__', '__len__',
        '__long__', '__lshift__', '__lt__', '__mod__', '__mul__', '__ne__',
        '__neg__', '__oct__', '__or__', '__pos__', '__pow__', '__radd__',
        '__rand__', '__rdiv__', '__rdivmod__', '__reduce__', '__reduce_ex__',
        '__repr__', '__reversed__', '__rfloorfiv__', '__rlshift__', '__rmod__',
        '__rmul__', '__ror__', '__rpow__', '__rrshift__', '__rshift__', '__rsub__',
        '__rtruediv__', '__rxor__', '__setitem__', '__setslice__', '__sub__',
        '__truediv__', '__xor__', 'next', '__hash__'
    ]
    
    def __new__(cls, classname, bases, attrs):
        overrides = attrs.get('__overrides__', [])
        overrides.extend(attrs.get('__slots__', []))
        overrides.extend(k for k in attrs.keys() if k not in
                         ['__overrides__'])
        for base in bases:
            overrides.extend(getattr(base, '__overrides__', []))
        assert '_wrapped' in overrides
        attrs['__overrides__'] = overrides
        
        def make_method(name):
            def method(self, *args, **kwargs):
                mtd = getattr(object.__getattribute__(self, "_wrapped"), name)
                return mtd(*args, **kwargs)
            return method

        for name in cls._special_names:
            if name not in overrides:
                attrs[name] = make_method(name)
        return type.__new__(cls, classname, bases, attrs)


class ProxyObject(metaclass=ProxyMeta):
    r"""Proxy for another object."""
    # http://code.activestate.com/recipes/496741-object-proxying/
    
    __slots__ = ["_wrapped", "__weakref__"]
    
    def __init__(self, wrapped):
        object.__setattr__(self, "_wrapped", wrapped)

    def __getattribute__(self, name):
        if name in object.__getattribute__(self, '__overrides__'):
            return object.__getattribute__(self, name)
        return getattr(object.__getattribute__(self, "_wrapped"), name)
    
    def __delattr__(self, name):
        if name in object.__getattribute__(self, '__overrides__'):
            object.__delattr__(self, name)
            return
        delattr(object.__getattribute__(self, "_wrapped"), name)
        
    def __setattr__(self, name, value):
        if name in object.__getattribute__(self, '__overrides__'):
            object.__setattr__(self, name, value)
            return
        setattr(object.__getattribute__(self, "_wrapped"), name, value)

    def __reduce__(self):
        return (object.__getattribute__(self, "__class__"),
                (object.__getattribute__(self, "_wrapped"), ))

    def __reduce_ex__(self, proto):
        return object.__getattribute__(self, "__reduce__")()
    
    # Special cases
    def __bool__(self):
        return bool(object.__getattribute__(self, "_wrapped"))
    
    def __str__(self):
        return str(object.__getattribute__(self, "_wrapped"))
    
    def __bytes__(self):
        return bytes(object.__getattribute__(self, "_wrapped"))
    
    def __repr__(self):
        return repr(object.__getattribute__(self, "_wrapped"))


class YggPopen(subprocess.Popen):
    r"""Uses Popen to open a process without a buffer. If not already set,
    the keyword arguments 'bufsize', 'stdout', and 'stderr' are set to
    0, subprocess.PIPE, and subprocess.STDOUT respectively. This sets the
    output stream to unbuffered and directs both stdout and stderr to the
    stdout pipe. In addition this class overrides Popen.kill() to allow
    processes to be killed with CTRL_BREAK_EVENT on windows.

    Args:
        args (list, str): Shell command or list of arguments that should be
            run.
        forward_signals (bool, optional): If True, flags will be set such
            that signals received by the spawning process will be forwarded
            to the child process. If False, the signals will not be forwarded.
            Defaults to True.
        **kwargs: Additional keywords arguments are passed to Popen.

    """
    def __init__(self, cmd_args, forward_signals=True, for_matlab=False, **kwargs):
        # stdbuf only for linux
        if platform._is_linux:
            stdbuf_args = ['stdbuf', '-o0', '-e0']
            if isinstance(cmd_args, str):
                cmd_args = ' '.join(stdbuf_args + [cmd_args])
            else:
                cmd_args = stdbuf_args + cmd_args
        kwargs.setdefault('bufsize', 0)
        kwargs.setdefault('stdout', subprocess.PIPE)
        kwargs.setdefault('stderr', subprocess.STDOUT)
        # To prevent forward of signals, process will have a new process group
        if not forward_signals:
            if platform._is_win:  # pragma: windows
                # TODO: Make sure that Matlab handled correctly since pty not
                # guaranteed on windows
                kwargs.setdefault('preexec_fn', None)
                kwargs.setdefault('creationflags',
                                  subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                if for_matlab:  # pragma: matlab
                    import pty
                    # Matlab requires a tty so a pty is used here to allow
                    # the process to be lanched in a new process group.
                    # Related Materials:
                    # - https://www.mathworks.com/matlabcentral/answers/
                    #       359992-system-call-bizarre-behavior
                    # - https://gist.github.com/thepaul/1206753
                    # - https://stackoverflow.com/questions/30139401/
                    #       filter-out-command-that-needs-a-terminal-in-python-
                    #       subprocess-module
                    parent_fd, child_fd = pty.openpty()
                    kwargs.setdefault('stdin', child_fd)
                    self.pty = (parent_fd, child_fd)

                kwargs.setdefault('preexec_fn', os.setpgrp)
        # if platform._is_win:  # pragma: windows
        #     kwargs.setdefault('universal_newlines', True)
        super(YggPopen, self).__init__(cmd_args, **kwargs)

    def disconnect(self):
        r"""Disconnect objects using resources."""
        if hasattr(self, 'pty'):  # pragma: matlab
            os.close(self.pty[0])
            os.close(self.pty[1])
            del self.pty

    def __del__(self, *args, **kwargs):
        self.disconnect()
        super(YggPopen, self).__del__(*args, **kwargs)

    def kill(self, *args, **kwargs):
        r"""On windows using CTRL_BREAK_EVENT to kill the process."""
        if platform._is_win:  # pragma: windows
            self.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            super(YggPopen, self).kill(*args, **kwargs)


def popen_nobuffer(*args, **kwargs):
    r"""Uses Popen to open a process without a buffer. If not already set,
    the keyword arguments 'bufsize', 'stdout', and 'stderr' are set to
    0, subprocess.PIPE, and subprocess.STDOUT respectively. This sets the
    output stream to unbuffered and directs both stdout and stderr to the
    stdout pipe.

    Args:
        args (list, str): Shell command or list of arguments that should be
            run.
        forward_signals (bool, optional): If True, flags will be set such
            that signals received by the spawning process will be forwarded
            to the child process. If False, the signals will not be forwarded.
            Defaults to True.
        **kwargs: Additional keywords arguments are passed to Popen.

    Returns:
        YggPopen: Process that was started.

    """
    return YggPopen(*args, **kwargs)


def pprint_encoded(obj, *args, **kwargs):
    r"""Pretty print an object, catching encoding errors as necessary.

    Args:
        obj (object): Python object to pprint.
        *args: Additional arguments are passed to pprint.pformat.
        **kwargs: Additional keyword arguments are passed to pprint.pformat.

    """
    print_encoded(pprint.pformat(obj, *args, **kwargs))


def print_encoded(msg, *args, **kwargs):
    r"""Print bytes to stdout, encoding if possible.

    Args:
        msg (str, bytes): Message to print.
        *args: Additional arguments are passed to print.
        **kwargs: Additional keyword arguments are passed to print.


    """
    if not isinstance(msg, (str, bytes)):
        msg = str(msg)
    try:
        print(bytes2str(msg), *args, **kwargs)
    except (UnicodeEncodeError, UnicodeDecodeError):  # pragma: debug
        logger.debug("sys.stdout.encoding = %s, cannot print unicode",
                     sys.stdout.encoding)
        kwargs.pop('end', None)
        try:
            print(msg, *args, **kwargs)
        except UnicodeEncodeError:  # pragma: debug
            print(str2bytes(msg), *args, **kwargs)


def import_all_modules(base=None, exclude=None, do_first=None):
    r"""Import all yggdrasil modules.

    Args:
        base (str, optional): Base module to start from. Defaults to
            'yggdrasil'.
        exclude (list, optional): Modules that should not be imported.
            Defaults to empty list.
        do_first (list, optional): Modules that should be import first.
            Defaults to empty list.

    """
    if base is None:
        base = 'yggdrasil'
    if exclude is None:
        exclude = []
    if do_first is None:
        do_first = []
    assert base.startswith('yggdrasil')
    for x in do_first:
        import_all_modules(x, exclude=exclude)
    exclude = exclude + do_first + ['yggdrasil.pytest_plugin']
    directory = os.path.dirname(__file__)
    parts = base.split('.')[1:]
    if parts:
        directory = os.path.join(directory, *parts)
    if not os.path.isfile(os.path.join(directory, '__init__.py')):
        return
    if (base in exclude) or base.endswith('tests'):
        return
    importlib.import_module(base)
    for x in sorted(glob.glob(os.path.join(directory, '*.py'))):
        x_base = os.path.basename(x)
        if x_base.startswith('__') and x_base.endswith('__.py'):
            continue
        x_mod = f"{base}.{os.path.splitext(os.path.basename(x))[0]}"
        if x_mod in exclude:
            continue
        importlib.import_module(x_mod)
    for x in sorted(glob.glob(os.path.join(directory, '*', ''))):
        if x.startswith('__') and x.endswith('__'):  # pragma: debug
            continue
        next_module = os.path.basename(os.path.dirname(x))
        import_all_modules(f"{base}.{next_module}",
                           exclude=exclude + do_first)


class TimeOut(object):
    r"""Class for checking if a period of time has been elapsed.

    Args:
        max_time (float, bbol): Maximum period of time that should elapse before
            'is_out' returns True. If False, 'is_out' will never return True.
            Providing 0 indicates that 'is_out' should immediately return True.
        key (str, optional): Key that was used to register the timeout. Defaults
            to None.

    Attributes:
        max_time (float): Maximum period of time that should elapsed before
            'is_out' returns True.
        start_time (float): Result of time.time() at start.
        key (str): Key that was used to register the timeout.

    """

    def __init__(self, max_time, key=None):
        self.max_time = max_time
        self.start_time = time.perf_counter()
        self.key = key
        self.checked = False

    @property
    def elapsed(self):
        r"""float: Total time that has elapsed since the start."""
        return time.perf_counter() - self.start_time
    
    @property
    def is_out(self):
        r"""bool: True if there is not any time remaining. False otherwise."""
        if self.max_time is False:
            return False
        if (not self.checked) and (self.max_time == 0):
            out = False
        else:
            out = (self.elapsed > self.max_time)
        self.checked = True
        return out


# def single_use_method(func):
#     r"""Decorator for marking functions that should only be called once."""
#     def wrapper(*args, **kwargs):
#         if getattr(func, '_single_use_method_called', False):
#             logger.info("METHOD %s ALREADY CALLED" % func)
#             return
#         else:
#             func._single_use_method_called = True
#             return func(*args, **kwargs)
#     return wrapper


class YggLoggerAdapter(logging.LoggerAdapter):
    r"""Logger adapter for use with YggClass."""

    def __init__(self, class_name, instance_name, *args, **kwargs):
        self._class_name = class_name
        self._instance_name = instance_name
        super(YggLoggerAdapter, self).__init__(*args, **kwargs)
    
    def process(self, msg, kwargs):
        r"""Process logging message."""
        if _stack_in_log:  # pragma: no cover
            stack = inspect.stack()
            the_class = os.path.splitext(os.path.basename(
                stack[2][0].f_globals["__file__"]))[0]
            the_line = stack[2][2]
            the_func = stack[2][3]
            prefix = '%s(%s).%s[%d]' % (the_class,
                                        self._instance_name,
                                        the_func, the_line)
        else:
            prefix = '%s(%s)' % (self._class_name,
                                 self._instance_name)
        new_msg = '%s: %s' % (prefix, self.as_str(msg))
        return new_msg, kwargs

    def as_str(self, obj):
        r"""Return str version of object if it is not already a string.

        Args:
            obj (object): Object that should be turned into a string.

        Returns:
            str: String version of provided object.

        """
        if not isinstance(obj, str):
            obj_str = str(obj)
        else:
            obj_str = obj
        return obj_str


class YggClass(ComponentBase):
    r"""Base class for Ygg classes.

    Args:
        name (str): Name used for component in log messages.
        uuid (str, optional): Unique ID for this instance. Defaults to None
            and is assigned.
        working_dir (str, optional): Working directory. If not provided, the
            current working directory is used.
        timeout (float, optional): Maximum time (in seconds) that should be
            spent waiting on a process. Defaults to 60.
        sleeptime (float, optional): Time that class should sleep for when
            sleep is called. Defaults to 0.01.
        **kwargs: Additional keyword arguments are passed to the ComponentBase
            initializer.

    Attributes:
        name (str): Class name.
        uuid (str): Unique ID for this instance.
        sleeptime (float): Time that class should sleep for when sleep called.
        longsleep (float): Time that the class will sleep for when waiting for
            longer tasks to complete (10x longer than sleeptime).
        timeout (float): Maximum time that should be spent waiting on a process.
        working_dir (str): Working directory.
        errors (list): List of errors.
        sched_out (obj): Output from the last scheduled task with output.
        logger (logging.Logger): Logger object for this object.
        suppress_special_debug (bool): If True, special_debug log messages
            are suppressed.

    """

    _base_defaults = ['name', 'uuid', 'working_dir', 'timeout', 'sleeptime']

    def __init__(self, name=None, uuid=None, working_dir=None,
                 timeout=60.0, sleeptime=0.01, **kwargs):
        # Defaults
        if name is None:
            name = ''
        if uuid is None:
            uuid = str(uuid_gen.uuid4())
        if working_dir is None:
            working_dir = os.getcwd()
        # Assign attributes
        self._name = name
        self.uuid = uuid
        self.sleeptime = sleeptime
        self.longsleep = self.sleeptime * 10
        self.timeout = timeout
        self._timeouts = {}
        self.working_dir = working_dir
        self.errors = []
        self.sched_out = None
        self.suppress_special_debug = False
        self._periodic_logs = {}
        self._old_loglevel = None
        self._old_encoding = None
        self.debug_flag = False
        # Call super class, adding in schema properties
        for k in self._base_defaults:
            if k in self._schema_properties:
                kwargs[k] = getattr(self, k)
        super(YggClass, self).__init__(**kwargs)
        self.logger = YggLoggerAdapter(
            self.__class__.__name__, self.print_name,
            logging.getLogger(self.__module__), {})

    def __getstate__(self):
        state = super(YggClass, self).__getstate__()
        del state['logger']
        # thread_attr = {}
        for k, v in list(state.items()):
            if isinstance(v, (threading._CRLock, threading._RLock,
                              threading.Event, threading.Thread)):  # pragma: debug
                self.warning("Special treatment of threading objects "
                             "currently disabled.")
            # if isinstance(v, (threading._CRLock, threading._RLock)):
            #     thread_attr.setdefault('threading.RLock', [])
            #     thread_attr['threading.RLock'].append((k, (), {}))
            # elif isinstance(v, threading.Event):
            #     thread_attr.setdefault('threading.Event', [])
            #     thread_attr['threading.Event'].append((k, (), {}))
            # elif isinstance(v, threading.Thread):
            #     assert(not v.is_alive())
            #     attr = {'name': v._name, 'group': None,
            #             'daemon': v.daemon, 'target': v._target,
            #             'args': v._args, 'kwargs': v._kwargs}
            #     thread_attr.setdefault('threading.Thread', [])
            #     thread_attr['threading.Thread'].append((k, (), attr))
        # for attr_list in thread_attr.values():
        #     for k in attr_list:
        #         state.pop(k[0])
        # state['thread_attr'] = thread_attr
        return state

    def __setstate__(self, state):
        super(YggClass, self).__setstate__(state)
        self.logger = YggLoggerAdapter(
            self.__class__.__name__, self.print_name,
            logging.getLogger(self.__module__), {})

    def __deepcopy__(self, memo):
        r"""Don't deep copy since threads cannot be copied."""
        return self

    @property
    def name(self):
        r"""str: Name of the class object."""
        return self._name

    @property
    def print_name(self):
        r"""str: Name of the class object."""
        return self._name.replace('%', '%%')

    def language_info(self, languages):
        r"""Only do info debug message if the language is one of those specified."""
        if not isinstance(languages, (list, tuple)):
            languages = [languages]
        languages = [lang.lower() for lang in languages]
        if get_subprocess_language().lower() in languages:  # pragma: debug
            return self.logger.info
        else:
            return self.dummy_log

    @property
    def interface_info(self):
        r"""Only do info debug message if is interface."""
        if is_subprocess():  # pragma: debug
            return self.logger.info
        else:
            return self.dummy_log

    def debug_log(self):  # pragma: debug
        r"""Turn on debugging."""
        self.info("Setting debug_log")
        from yggdrasil.config import get_ygg_loglevel, set_ygg_loglevel
        self._old_loglevel = get_ygg_loglevel()
        set_ygg_loglevel('DEBUG')

    def reset_log(self):  # pragma: debug
        r"""Resetting logging to prior value."""
        from yggdrasil.config import set_ygg_loglevel
        if self._old_loglevel is not None:
            set_ygg_loglevel(self._old_loglevel)

    def pprint(self, obj, block_indent=0, indent_str='    ', **kwargs):
        r"""Use pprint to represent an object as a string.

        Args:
            obj (object): Python object to represent.
            block_indent (int, optional): Number of indents that should be
                placed in front of the entire block. Defaults to 0.
            indent_str (str, optional): String that should be used to indent.
                Defaults to 4 spaces.
            **kwargs: Additional keyword arguments are passed to pprint.pformat.

        Returns:
            str: String representation of object using pprint.

        """
        sblock = block_indent * indent_str
        out = sblock + pprint.pformat(obj, **kwargs).replace('\n', '\n' + sblock)
        return out

    def display(self, msg='', *args, **kwargs):
        r"""Print a message, no log."""
        msg, kwargs = self.logger.process(msg, kwargs)
        print(msg % args)

    def verbose_debug(self, *args, **kwargs):
        r"""Log a verbose debug level message."""
        return self.logger.log(9, *args, **kwargs)
        
    def dummy_log(self, *args, **kwargs):
        r"""Dummy log function that dosn't do anything."""
        pass

    def periodic_debug(self, key, period=10):
        r"""Log that should occur periodically rather than with every call.

        Arguments:
            key (str): Key that should be used to identify the debug message.
            period (int, optional): Period (in number of messages) that messages
                should be logged at. Defaults to 10.

        Returns:
            method: Logging method to be used.

        """
        if key in self._periodic_logs:
            self._periodic_logs[key] += 1
        else:
            self._periodic_logs[key] = 0
        if (self._periodic_logs[key] % period) == 0:
            return self.logger.debug
        else:
            return self.dummy_log

    @property
    def special_debug(self):
        r"""Log debug level message contingent of supression flag."""
        if not self.suppress_special_debug:
            return self.logger.debug
        else:
            return self.dummy_log

    @property
    def info(self):
        r"""Log an info level message."""
        return self.logger.info

    @property
    def debug(self):
        r"""Log a debug level message."""
        return self.logger.debug

    @property
    def critical(self):
        r"""Log a critical level message."""
        return self.logger.critical

    @property
    def warn(self):
        r"""Log a warning level message."""
        return self.logger.warning

    @property
    def warning(self):
        r"""Log a warning level message."""
        return self.logger.warning

    @property
    def error(self):
        r"""Log an error level message."""
        self.errors.append('ERROR')
        return self.logger.error
        # return super(YggClass, self).error

    @property
    def exception(self):
        r"""Log an exception level message."""
        exc_info = sys.exc_info()
        if exc_info is not None and exc_info != (None, None, None):
            self.errors.append('ERROR')
            return self.logger.exception
            # return super(YggClass, self).exception
        else:
            return self.error

    def print_encoded(self, msg, *args, **kwargs):
        r"""Print bytes to stdout, encoding if possible.

        Args:
            msg (str, bytes): Message to print.
            *args: Additional arguments are passed to print.
            **kwargs: Additional keyword arguments are passed to print.


        """
        return print_encoded(msg, *args, **kwargs)

    def printStatus(self, level='info', return_str=False):
        r"""Print the class status."""
        fmt = '%s(%s): '
        args = (self.__module__, self.print_name)
        if return_str:
            msg, _ = self.logger.process(fmt, {})
            return msg % args
        getattr(self.logger, level)(fmt, *args)

    def _task_with_output(self, func, *args, **kwargs):
        self.sched_out = func(*args, **kwargs)

    def sched_task(self, t, func, args=None, kwargs=None, store_output=False,
                   name=None):
        r"""Schedule a task that will be executed after a certain time has
        elapsed.

        Args:
            t (float): Number of seconds that should be waited before task
                is executed.
            func (object): Function that should be executed.
            args (list, optional): Arguments for the provided function.
                Defaults to [].
            kwargs (dict, optional): Keyword arguments for the provided
                function. Defaults to {}.
            store_output (bool, optional): If True, the output from the
                scheduled task is stored in self.sched_out. Otherwise, it is not
                stored. Defaults to False.
            name (str, optional): Name for the task.

        Returns:
            threading.Timer: The timer object.

        """
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        self.sched_out = None
        if store_output:
            args = [func] + args
            func = self._task_with_output
        tobj = threading.Timer(t, func, args=args, kwargs=kwargs)
        if name is not None:
            tobj.name = name
        tobj.start()
        return tobj

    def sleep(self, t=None):
        r"""Have the class sleep for some period of time.

        Args:
            t (float, optional): Time that class should sleep for. If not
                provided, the attribute 'sleeptime' is used.

        """
        if t is None:
            t = self.sleeptime
        sleep(t)

    @property
    def timeout_key(self):  # pragma: no cover
        r"""str: Key identifying calling object and method."""
        return self.get_timeout_key()

    def get_timeout_key(self, key_level=0, key_suffix=None):
        r"""Return a key for a given level in the stack, relative to the
        function calling get_timeout_key.

        Args:
            key_level (int, optional): Positive integer indicating the level of
                the calling class and function/method that should be used to
                key the timeout. 0 is the class and function/method that is 2
                steps higher in the stack. Higher values use classes and
                function/methods further up in the stack. Defaults to 0.
            key_suffix (str, optional): String that should be appended to the
                end of the generated key. Defaults to None and is ignored.

        Returns:
            str: Key identifying calling object and method.

        """
        if _stack_in_timeout:  # pragma: debug
            stack = inspect.stack()
            fcn = stack[key_level + 2][3]
            cls = os.path.splitext(os.path.basename(stack[key_level + 2][1]))[0]
            key = '%s(%s).%s.%s' % (cls, self.print_name, fcn,
                                    threading.current_thread().name)
        else:
            key = '%s(%s).%s' % (str(self.__class__).split("'")[1], self.print_name,
                                 threading.current_thread().name)
        if key_suffix is not None:
            key += key_suffix
        return key

    def wait_on_function(self, function, timeout=None, polling_interval=None,
                         key=None, key_level=0, key_suffix=None, quiet=False):
        r"""Wait util a function returns True or a time limit is reached.

        Args:
            t (float, optional): Maximum time that the calling function should
                wait before timeing out. If not provided, the attribute
                'timeout' is used.
            key (str, optional): Key that should be associated with the timeout
                that is created. Defaults to None and is set by the calling
                class and function/method (See `get_timeout_key`).
            key_level (int, optional): Positive integer indicating the level of
                the calling class and function/method that should be used to
                key the timeout. 0 is the class and function/method that called
                start_timeout. Higher values use classes and function/methods
                further up in the stack. Defaults to 0.
            key_suffix (str, optional): String that should be appended to the
                end of the generated key. Defaults to None and is ignored.
            quiet (bool, optional): If True, error message on timeout exceeded
                will be debug log. Defaults to False.

        Raises:
            KeyError: If the key already exists.

        """
        from yggdrasil import multitasking
        if timeout is None:
            timeout = self.timeout
        elif timeout is False:
            timeout = None
        if polling_interval is None:
            polling_interval = self.sleeptime
        if key is None:
            key = self.get_timeout_key(key_level=key_level, key_suffix=key_suffix)
        try:
            out = multitasking.wait_on_function(
                function, timeout=timeout, polling_interval=polling_interval)
        except multitasking.TimeoutError as e:
            out = e.function_value
            msg = "Timeout for %s at %5.2f s" % (key, timeout)
            if quiet:
                self.debug(msg)
            else:
                self.info(msg)
        return out

    def start_timeout(self, t=None, key=None, key_level=0, key_suffix=None):
        r"""Start a timeout for the calling function/method.

        Args:
            t (float, optional): Maximum time that the calling function should
                wait before timeing out. If not provided, the attribute
                'timeout' is used.
            key (str, optional): Key that should be associated with the timeout
                that is created. Defaults to None and is set by the calling
                class and function/method (See `get_timeout_key`).
            key_level (int, optional): Positive integer indicating the level of
                the calling class and function/method that should be used to
                key the timeout. 0 is the class and function/method that called
                start_timeout. Higher values use classes and function/methods
                further up in the stack. Defaults to 0.
            key_suffix (str, optional): String that should be appended to the
                end of the generated key. Defaults to None and is ignored.

        Raises:
            KeyError: If the key already exists.

        """
        if t is None:
            t = self.timeout
        if key is None:
            key = self.get_timeout_key(key_level=key_level, key_suffix=key_suffix)
        if key in self._timeouts:
            raise KeyError("Timeout already registered for %s" % key)
        self._timeouts[key] = TimeOut(t, key=key)
        return self._timeouts[key]

    def check_timeout(self, key=None, key_level=0):
        r"""Check timeout for the calling function/method.

        Args:
            key (str, optional): Key for timeout that should be checked.
                Defaults to None and is set by the calling class and
                function/method (See `timeout_key`).
            key_level (int, optional): Positive integer indicating the level of
                the calling class and function/method that should be used to
                key the timeout. 0 is the class and function/method that called
                start_timeout. Higher values use classes and function/methods
                further up in the stack. Defaults to 0.

        Raises:
            KeyError: If there is not a timeout registered for the specified
                key.

        """
        if key is None:
            key = self.get_timeout_key(key_level=key_level)
        if key not in self._timeouts:
            raise KeyError("No timeout registered for %s" % key)
        t = self._timeouts[key]
        return t.is_out
        
    def stop_timeout(self, key=None, key_level=0, key_suffix=None, quiet=False):
        r"""Stop a timeout for the calling function method.

        Args:
            key (str, optional): Key for timeout that should be stopped.
                Defaults to None and is set by the calling class and
                function/method (See `timeout_key`).
            key_level (int, optional): Positive integer indicating the level of
                the calling class and function/method that should be used to
                key the timeout. 0 is the class and function/method that called
                start_timeout. Higher values use classes and function/methods
                further up in the stack. Defaults to 0.
            key_suffix (str, optional): String that should be appended to the
                end of the generated key. Defaults to None and is ignored.
            quiet (bool, optional): If True, error message on timeout exceeded
                will be debug log. Defaults to False.

        Raises:
            KeyError: If there is not a timeout registered for the specified
                key.

        """
        if key is None:
            key = self.get_timeout_key(key_level=key_level, key_suffix=key_suffix)
        if key not in self._timeouts:
            raise KeyError("No timeout registered for %s" % key)
        t = self._timeouts[key]
        if t.is_out and t.max_time > 0:
            if quiet:
                self.debug("Timeout for %s at %5.2f/%5.2f s" % (
                    key, t.elapsed, t.max_time))
            else:
                self.info("Timeout for %s at %5.2f/%5.2f s" % (
                    key, t.elapsed, t.max_time))
        del self._timeouts[key]


class CacheDirMixin:
    r"""Base class for managing the cache_dir.

    Args:
        cache_dir (str, optional): Directory where the original file or
            directory should be cached for generated files that replace
            existing files or directories. Defaults to a _ygg_cache
            subdirectory in the directory containing the original if not
            provided.

    """

    def __init__(self, *args, **kwargs):
        self.cache_dir = kwargs.pop('cache_dir', None)
        self.inherited_cache_dir = isinstance(self.cache_dir,
                                              GeneratedDirectory)
        self.init_cache_dir()
        super().__init__(*args, **kwargs)

    def init_cache_dir(self, *args, **kwargs):
        r"""Initialize the cache directory."""
        if self.cache_dir is None and args:
            base_dir = os.path.dirname(args[0])
            if kwargs.get('create_parent_dir', False):
                base_dir = os.path.dirname(base_dir)
            self.cache_dir = os.path.join(base_dir, '_ygg_cache')
        if isinstance(self.cache_dir, str):
            self.cache_dir = GeneratedDirectory(self.cache_dir)
        return bool(self.cache_dir)

    def setup_cache_dir(self):
        r"""Create the cache directory if it doesn't exist."""
        if self.init_cache_dir():
            self.cache_dir.setup()

    def teardown_cache_dir(self):
        r"""Remove the cache directory if it was created."""
        if (not self.inherited_cache_dir) and self.init_cache_dir():
            self.cache_dir.teardown()


class IntegrationPathSet(CacheDirMixin):
    r"""Class for managing a set of files or directories created during an
    integration.

    Args:
        products (list, optional): Products to initialize the set with.
        overwrite (bool, optional): If True, overwrite any existing file
            or directory with the specified name by removing it during
            setup.
        cache_dir (str, optional): Directory where the original file or
            directory should be cached for generated files that replace
            existing files or directories. Defaults to a _ygg_cache
            subdirectory in the directory containing the original if not
            provided.
        removable_source_exts (tuple, optional): Source extensions that
            can be removed. Attempting to remove source files with any
            other extensions (as defined by constants.ALL_LANGUAGE_EXTS)
            will raise a RuntimeError.
        generalized_suffix (str, optional): Suffix to replace with * in
            associated paths in order to search for related paths that
            should also be managed.
        lock (callable, optional): Context manager that should be used
            during setup and teardown operations.

    """

    def __init__(self, products=None, overwrite=False, cache_dir=None,
                 removable_source_exts=None, generalized_suffix=None,
                 lock=None):
        super(IntegrationPathSet, self).__init__(cache_dir=cache_dir)
        self.overwrite = overwrite
        self.removable_source_exts = removable_source_exts
        self._generalized_suffix = generalized_suffix
        if self.removable_source_exts is None:
            self.removable_source_exts = tuple([])
        self.paths = []
        self.last_idx = -1
        self.lock = lock
        if products:
            for x in products:
                self.append(x)

    def __str__(self):
        return 'IntegrationPathSet([' + ', '.join(
            [str(x) for x in self.paths]) + '])'

    @property
    def generalized_suffix(self):
        r"""str: Suffix to replace with * to remove additional paths."""
        return self._generalized_suffix

    @generalized_suffix.setter
    def generalized_suffix(self, value):
        self._generalized_suffix = value
        for x in self.paths:
            x.generalized_suffix = value

    def index(self, name):
        r"""Determine the index of a path in the set.

        Args:
            name (str): Path to locate.

        Returns:
            int: Index of the path in the set if it is present, -1 if it
                is not present.

        """
        for i, x in enumerate(self.paths):
            if x.name == name:
                return i
        return -1

    def append(self, name, *args, **kwargs):
        r"""Append a IntegrationPath to this set."""
        move_existing = kwargs.pop('move_existing', False)
        assert isinstance(name, str)
        idx = self.index(name)
        cls = kwargs.pop('cls', IntegrationPath)
        kwargs.setdefault('overwrite', self.overwrite)
        kwargs.setdefault('removable_source_exts',
                          self.removable_source_exts)
        kwargs.setdefault('generalized_suffix', self.generalized_suffix)
        if move_existing and idx != -1:
            path = self.paths[idx]
            del self.paths[idx]
            idx = -1
        else:
            path = cls(name, *args, **kwargs)
        if idx == -1:
            self.last_idx = len(self.paths)
            self.paths.append(path)
        else:
            self.last_idx = idx
            self.paths[idx] = path

    def append_generated(self, *args, **kwargs):
        r"""Append a GeneratedFile to this path set."""
        kwargs.setdefault('cls', GeneratedFile)
        self.init_cache_dir(*args, **kwargs)
        kwargs.setdefault('cache_dir', self.cache_dir)
        return self.append(*args, **kwargs)

    def append_compilation_product(self, *args, **kwargs):
        r"""Append a CompilationProduct to this path set."""
        kwargs['cls'] = CompilationProduct
        return self.append(*args, **kwargs)

    @property
    def products(self):
        r"""Products to remove during setup when overwrite is set or
        during teardown."""
        out = []
        if self.cache_dir:
            out += self.cache_dir.products
        for x in self.paths:
            out += x.products
        return out

    @property
    def root(self):
        r"""str: Root directory containing all products in the set."""
        out = None
        for k in self.products:
            if platform._is_win and '/' in k:
                k = k.replace('/', os.path.sep)
            if not (k and os.path.isabs(k)):
                continue
            if out is None:
                out = k
                continue
            while out and not k.startswith(out):
                out = os.path.dirname(out)
        return out

    @contextlib.contextmanager
    def locked(self):
        r"""Acquire the lock for the set."""
        if self.lock:
            with self.lock():
                yield
        else:
            yield

    def setup(self, tag=None):
        r"""Perform actions on the paths before an integration run.

        Args:
            tag (str, optional): Only perform actions for paths with the
                provided tag.

        """
        with self.locked():
            self.setup_cache_dir()
            for x in self.paths:
                if x.tag == tag:
                    x.setup()

    def teardown(self, tag=None):
        r"""Perform actions to cleanup the paths after an integration run.

        Args:
            tag (str, optional): Only perform actions for paths with the
                provided tag.

        """
        with self.locked():
            for x in self.paths:
                if x.tag == tag:
                    x.teardown()
            self.teardown_cache_dir()

    def restore_modified(self, tag=None):
        r"""Restore modified original files.

        Args:
            tag (str, optional): Only perform actions for paths with the
                provided tag.

        """
        for x in self.paths:
            if x.tag == tag:
                x.restore_modified()
        self.teardown_cache_dir()

    @property
    def last(self):
        r"""IntegrationPath: The last path added to the set."""
        assert self.last_idx >= 0
        return self.paths[self.last_idx]


class IntegrationPath(object):
    r"""Class for handling generation and managment of paths associated
    with integrations.

    Args:
        name (str): Root path name for the file or directory.
        overwrite (bool, optional): If True, overwrite any existing path
            with the specified name.
        additional_products (list, optional): Additional products that
            should be associated with the path and removed on cleanup.
        removable_source_exts (tuple, optional): Source extensions that
            can be removed. Attempting to remove source files with any
            other extensions (as defined by constants.ALL_LANGUAGE_EXTS)
            will raise a RuntimeError.
        generalized_suffix (str, optional): Suffix to replace with * in
            associated paths in order to search for related paths that
            should also be managed.
        skip_source_check (bool, optional): If True, the products will
            not be checked for source files prior to be removed.
        tag (str, optional): Tag that should be added to the path for
            performing tags on subsets of files.
        create_parent_dir (bool, optional): If True, create the path's
            parent directory if it does not exist.
        **kwargs: Additional keyword arguments are ignored.

    """

    def __init__(self, name, overwrite=False, additional_products=None,
                 removable_source_exts=None, generalized_suffix=None,
                 skip_source_check=False, tag=None,
                 create_parent_dir=False, **kwargs):
        self.name = name
        self.overwrite = overwrite
        self.additional_products = additional_products
        self.removable_source_exts = removable_source_exts
        self.generalized_suffix = generalized_suffix
        self.skip_source_check = skip_source_check
        self.tag = tag
        self.create_parent_dir = create_parent_dir
        if self.additional_products is None:
            self.additional_products = []
        if self.removable_source_exts is None:
            self.removable_source_exts = tuple([])
        self.removed = False
        if self.create_parent_dir:
            self.create_parent_dir = GeneratedDirectory(
                os.path.dirname(self.name))

    def __str__(self):
        return self.name

    @property
    def products(self):
        r"""Products to remove during setup when overwrite is set or
        during teardown."""
        return [self.name] + self.additional_products

    @property
    def generalized_products(self):
        r"""Related products based on generalized_suffix to remove during
        setup when overwrite is set or during teardown."""
        if not self.generalized_suffix:
            return []
        out = []
        for x in self.products:
            if self.generalized_suffix in x:
                for alt in glob.glob(x.replace(self.generalized_suffix, '*')):
                    if alt not in self.products:
                        out.append(alt)
        return out

    @property
    def exists(self):
        r"""bool: True if the file or directory exists."""
        return (os.path.isfile(self.name) or os.path.isdir(self.name))

    def setup(self):
        r"""Perform actions on the path before an integration."""
        if self.overwrite:
            self.remove_products()
        if self.create_parent_dir:
            self.create_parent_dir.setup()

    def teardown(self):
        r"""Perform actions to cleanup the path after an integration."""
        self.remove_products()
        if self.create_parent_dir:
            self.create_parent_dir.teardown()

    @property
    def split_sources(self):
        r"""tuple: Products that can contain sources and those that cannot."""
        out = {'allowed': [], 'disallowed': []}
        for x in self.products + self.generalized_products:
            if x.endswith(self.removable_source_exts):
                out['allowed'].append(x)
            else:
                out['disallowed'].append(x)
        return out

    def remove_products(self):
        r"""Remove products associated with the managed path."""
        split_sources = self.split_sources
        for x in split_sources['allowed']:
            self.remove_product(x, skip_source_check=True)
        for x in split_sources['disallowed']:
            self.remove_product(x)
        if self.exists:  # pragma: debug
            raise RuntimeError(f"Product not removed: {self.name}")
        self.removed = True

    def restore_modified(self):
        r"""Restore modified original files."""
        pass

    def remove_product(self, product, skip_source_check=None):
        r"""Remove a single product.

        Args:
            product (str): Product to remove.

        """
        logger.debug(f"Removing product {product}")
        if skip_source_check is None:
            skip_source_check = self.skip_source_check
        if not skip_source_check:
            src = self.find_source_files(product)
            if src:
                raise RuntimeError(f"Removing product would remove "
                                   f"source files {src}")
        remove_path(product)

    def find_source_files(self, product):
        r"""Check for sources files in the managed path.

        Args:
            product (str): Path to check.

        Returns:
            list: Paths to located source files.

        """
        out = []
        source_keys = copy.copy(constants.ALL_LANGUAGE_EXTS)
        if '.exe' in source_keys:  # pragma: windows
            source_keys.remove('.exe')
        if os.path.isdir(product):
            ext_tuple = tuple(source_keys)
            for root, dirs, files in os.walk(product):
                for f in files:
                    tmp = os.path.join(root, f)
                    if tmp.endswith(ext_tuple):
                        out += self.find_source_files(tmp)
        elif (os.path.isfile(product)
              and os.path.splitext(product)[-1] in source_keys):
            out.append(product)
        return out


class GeneratedDirectory(IntegrationPath):
    r"""Class for handling generation of directories associated with an
    integration.

    Args:
        name (str): Root path for the directory.
        **kwargs: Additional keyword arguments are passed to the
            IntegrationPath constructor.

    """

    def __init__(self, name, **kwargs):
        kwargs.setdefault('skip_source_check', True)
        super(GeneratedDirectory, self).__init__(name, **kwargs)
        self.generated = False

    def setup(self):
        r"""Create the directory if it doesn't exist."""
        super(GeneratedDirectory, self).setup()
        if not os.path.isdir(self.name):
            self.generated = True
            os.mkdir(self.name)

    def remove_products(self):
        r"""Remove the directory if it was created."""
        if self.generated:
            assert not (self.exists and os.listdir(self.name))
            super(GeneratedDirectory, self).remove_products()
            self.generated = False


class GeneratedFile(CacheDirMixin, IntegrationPath):
    r"""Class for handling generation of files associated with integrations.

    Args:
        name (str): Root path name for the file.
        lines (list): List of lines that should be placed in the file.
        overwrite (bool, optional): If True, overwrite any existing file
            with the specified name. If replaces is True, the existing
            file will only be removed if the replaced file is preserved.
        replaces (bool, optional): If True, the file replaces any existing
            file that will be preserved and restored when the generated
            file is removed.
        verbose (bool, optional): If True, log information will be
            displayed when the file is generated.
        **kwargs: Additional keyword arguments are passed to the
            IntegrationPath constructor.
    
    """

    def __init__(self, name, lines, replaces=False,
                 verbose=False, **kwargs):
        kwargs.setdefault('skip_source_check', True)
        super().__init__(name, **kwargs)
        self.replaces = replaces
        self.lines = lines
        self.generated = False
        self.verbose = verbose
        if self.replaces:
            self.replaces = os.path.join(self.cache_dir.name,
                                         os.path.basename(name))

    def remove_products(self):
        r"""Remove products associated with the managed path, preserving
        the original first if one is being replaced and the cache
        doesn't exist."""
        if os.path.isfile(self.name):
            self.cache_original()
        super(GeneratedFile, self).remove_products()

    def cache_original(self):
        r"""Cache the original file."""
        if self.replaces and not os.path.isfile(self.replaces):
            self.setup_cache_dir()
            if not os.path.isfile(self.name):
                raise RuntimeError(f"Original file does not exist: {self.name}")
            shutil.move(self.name, self.replaces)
        
    def restore_modified(self):
        r"""Restore modified original files."""
        if self.replaces and os.path.isfile(self.replaces):
            shutil.move(self.replaces, self.name)
            log_msg = f"Restored original {self.name}"
            if self.verbose:
                logger.info(log_msg)
            else:
                logger.debug(log_msg)
            self.teardown_cache_dir()
        
    def setup(self):
        r"""Perform actions on the file before an integration run
        including generating the file."""
        self.cache_original()
        super(GeneratedFile, self).setup()
        if self.lines and not os.path.isfile(self.name):
            log_msg = (f'Generating {self.name}:\n\t'
                       + '\n\t'.join(self.lines))
            if self.verbose:
                logger.info(log_msg)
            else:
                logger.debug(log_msg)
            with open(self.name, 'w') as fd:
                fd.write('\n'.join(self.lines))
            self.generated = True

    def teardown(self):
        r"""Perform actions to cleanup the file after an integration run."""
        super(GeneratedFile, self).teardown()
        self.restore_modified()


class GeneratedShellScript(GeneratedFile):
    r"""Generated script that will be made executable.

    Args:
        exit_on_error (bool, optional): If True, the script will be
            generated so that it exits when there is an error.

    """

    def __init__(self, name, lines, exit_on_error=False, **kwargs):
        if name.endswith('.sh'):
            if '#!/bin/bash' not in lines:
                lines.insert(0, '#!/bin/bash')
        if exit_on_error:
            if name.endswith('.sh'):
                if 'set -e' not in lines:
                    lines.insert(1, 'set -e')
            elif name.endswith('.bat'):  # pragma: windows
                error_check = 'if %errorlevel% neq 0 exit /b %errorlevel%'
                for i in range(len(lines), 0, -1):
                    lines.insert(i, error_check)
        super(GeneratedShellScript, self).__init__(name, lines, **kwargs)

    def setup(self):
        r"""Perform actions on the file before an integration run
        including generating the file."""
        super(GeneratedShellScript, self).setup()
        if (not platform._is_win) and os.path.isfile(self.name):
            # mode = (stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            # os.chmod(self.name, mode)
            os.chmod(self.name, 0o755)

    def run(self, cmd=None, return_output=False, **kws):
        r"""Run the generated script, first generating it if necessary.

        Args:
            cmd (list, optional): Prefix arguments that should be used to
                run the script with the script file name appended.
            return_output (bool, optional): If True, the output from the
                generated script will be captured and returned.
            **kws: Additional keyword arguments are passed to
                subprocess.check_call (or subprocess.check_output if
                return_output is True).

        """
        generated = self.generated
        if not generated:
            self.setup()
        try:
            if cmd:
                cmd = cmd + [self.name]
            elif platform._is_win:  # pragma: windows
                cmd = [os.environ['COMSPEC'], '/c', 'call', self.name]
            else:
                cmd = []
                if os.path.isabs(self.name):
                    cmd.append(self.name)
                else:
                    cmd.append(f'./{self.name}')
            log_msg = f'RUNNING: {self.name}:\n\t' + '\n\t'.join(self.lines)
            if self.verbose:
                logger.info(log_msg)
            else:
                logger.debug(log_msg)
            if kws.get('shell', False):
                cmd = ' '.join(cmd)
            if return_output:
                return subprocess.check_output(cmd, **kws)
            else:
                subprocess.check_call(cmd, **kws)
        finally:
            if not generated:
                self.teardown()


def TemporaryGeneratedFile(lines, prefix='', suffix='', ext='.txt',
                           cls=GeneratedFile, **kwargs):
    r"""Class for generating a temporary generated file. The file name
    will be generated in the temporary directory.

    Args:
        lines (list): List of lines that should be placed in the file.
        prefix (str, optional): Prefix that will be added to the generated
            file name before the unique identifier.
        suffix (str, optional): Suffix that will be added to the generated
            file name after the unique identifier.
        ext (str, optional): File extension to use.
        **kwargs: Additional keyword arguments are passed to the
            GeneratedFile constructor.

    """
    import tempfile
    uuid = str(uuid_gen.uuid4())
    kwargs.setdefault('overwrite', True)
    assert not kwargs.get('replace', False)
    if ext is None and cls == GeneratedShellScript:
        if platform._is_win:  # pragma: windows
            ext = '.bat'
        else:
            ext = '.sh'
    name = os.path.join(tempfile.gettempdir(),
                        f'{prefix}{uuid}{suffix}{ext}')
    return cls(name, lines, **kwargs)


class CompilationProduct(IntegrationPath):
    r"""Class for handling management of compilation products.

    Args:
        name (str): Root path name for the compilation product.
        extensions (list, optional): List of extensions to add to the file
            base in name to generate additional product file names.
        files (list, optional): List of file names in directory to add
            to the list of associated products.
        directory (str, optional): Directory containing associated
            compilation products provided by files. Defaults to the
            directory containing name if not provided.
        is_directory (bool, optional): If True, name is a directory.
        sources (list, optional): List of sources files to exclude from
            the product list.
        **kwargs: Additional keyword arguments are passed to the IntegrationPath
            constructor.

    """

    def __init__(self, name, extensions=None, files=None,
                 directory=None, sources=None, is_directory=False,
                 create_directory=False, **kwargs):
        super(CompilationProduct, self).__init__(name, **kwargs)
        self.extensions = extensions
        self.files = files
        self.directory = directory
        self.sources = sources
        self.is_directory = is_directory
        self.create_directory = create_directory
        self.created_directory = False
        if self.extensions is None:
            self.extensions = []
        if self.files is None:
            self.files = []
        if self.directory is None:
            if self.is_directory:
                self.directory = self.name
            else:
                self.directory = os.path.dirname(self.name)
        if self.sources is None:
            self.sources = []
        self._products = [self.name] + self.additional_products
        base = os.path.splitext(self.name)[0]
        for x in self.extensions:
            inew = base + x
            if inew not in self._products:
                self._products.append(inew)
            inew = self.name + x
            if inew not in self._products:
                self._products.append(inew)
        for x in self.files:
            inew = os.path.join(self.directory, x)
            if inew not in self._products:
                self._products.append(inew)
        for x in self.sources:
            if x in self._products:
                self._products.remove(x)

    @property
    def products(self):
        r"""Products to remove during setup when overwrite is set or
        during teardown."""
        return copy.copy(self._products)

    @property
    def exists(self):
        r"""bool: True if the file or directory exists."""
        if self.is_directory and self.create_directory:
            contents = glob.glob(os.path.join(self.name, '*'))
            return bool(contents)
        return super(CompilationProduct, self).exists
        
    def setup(self):
        r"""Perform actions on the file before an integration run
        including generating the file."""
        super(CompilationProduct, self).setup()
        if ((self.create_directory and self.directory
             and not os.path.isdir(self.directory))):
            self.created_directory = True
            os.mkdir(self.directory)
            if self.directory not in self._products:
                self._products.append(self.directory)
