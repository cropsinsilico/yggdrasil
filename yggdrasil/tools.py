"""This modules offers various tools."""
from __future__ import print_function
import threading
import logging
import pprint
import os
import sys
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
import atexit
import uuid as uuid_gen
import subprocess
import importlib
from yggdrasil import platform
from yggdrasil.components import import_component, ComponentBase


logger = logging.getLogger(__name__)
YGG_MSG_EOF = b'EOF!!!'
YGG_MSG_BUF = 1024 * 2


_stack_in_log = False
_stack_in_timeout = False
if ((logging.getLogger("yggdrasil").getEffectiveLevel()
     <= logging.DEBUG)):  # pragma: debug
    _stack_in_log = False
    _stack_in_timeout = True
_thread_registry = {}
_lock_registry = {}
_main_thread = threading.main_thread()


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


def check_threads():  # pragma: debug
    r"""Check for threads that are still running."""
    global _thread_registry
    # logger.info("Checking %d threads" % len(_thread_registry))
    for k, v in _thread_registry.items():
        if v.is_alive():
            logger.error("Thread is alive: %s" % k)
    if threading.active_count() > 1:
        logger.info("%d threads running" % threading.active_count())
        for t in threading.enumerate():
            logger.info("%s thread running" % t.name)


def check_locks():  # pragma: debug
    r"""Check for locks in lock registry that are locked."""
    global _lock_registry
    # logger.info("Checking %d locks" % len(_lock_registry))
    for k, v in _lock_registry.items():
        res = v.acquire(False)
        if res:
            v.release()
        else:
            logger.error("Lock could not be acquired: %s" % k)


def check_sockets():  # pragma: debug
    r"""Check registered sockets."""
    from yggdrasil.communication import cleanup_comms
    count = cleanup_comms('ZMQComm')
    if count > 0:
        logger.info("%d sockets closed." % count)


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
    if libtype not in ['static', 'shared', None]:  # pragma: debug
        raise ValueError("libtype must be 'shared' or 'static', "
                         "'%s' not supported." % libtype)
    paths = sysconfig.get_paths()
    cvars = sysconfig.get_config_vars()
    if platform._is_win:  # pragma: windows
        if libtype is None:
            libtype = 'static'
        libtype2ext = {'shared': '.dll', 'static': '.lib'}
        base = 'python%s%s' % (cvars['py_version_nodot'],
                               libtype2ext[libtype])
    else:
        if libtype is None:
            libtype = 'shared'
        libtype2key = {'shared': 'LDLIBRARY', 'static': 'LIBRARY'}
        base = cvars.get(libtype2key[libtype], None)
        if platform._is_mac and base.endswith('/Python'):  # pragma: osx
            base = 'libpython%s.dylib' % cvars['py_version_short']
    if base is None:  # pragma: debug
        raise RuntimeError(("Could not determine base name for the Python "
                            "C API library.\n"
                            "sysconfig.get_paths():\n%s\n"
                            "sysconfig.get_config_vars():\n%s\n")
                           % (pprint.pformat(paths),
                              pprint.pformat(cvars)))
    dir_try = []
    if cvars['prefix']:
        dir_try.append(cvars['prefix'])
        if platform._is_win:  # pragma: windows
            dir_try.append(os.path.join(cvars['prefix'], 'libs'))
        else:
            dir_try.append(os.path.join(cvars['prefix'], 'lib'))
    if cvars.get('LIBDIR', None):
        dir_try.append(cvars['LIBDIR'])
    if cvars.get('LIBDEST', None):
        dir_try.append(cvars['LIBDEST'])
    for k in ['stdlib', 'purelib', 'platlib', 'platstdlib', 'data']:
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
    if allow_failure:  # pragma: debug
        return base
    raise RuntimeError(("Could not determine the location of the Python "
                        "C API library: %s.\n"
                        "sysconfig.get_paths():\n%s\n"
                        "sysconfig.get_config_vars():\n%s\n")
                       % (base, pprint.pformat(paths),
                          pprint.pformat(cvars)))  # pragma: debug


def get_conda_prefix():
    r"""Determine the conda path prefix for the current environment.

    Returns:
        str: Full path to the directory prefix used for the current conda
            environment if one exits. If conda cannot be located, None is
            returned.

    """
    conda_prefix = os.environ.get('CONDA_PREFIX', None)
    # This part should be enabled if the conda base enviroment dosn't have
    # CONDA_PREFIX set. Older version of conda behaved this way so it is
    # possible that a future release will as well.
    # if not conda_prefix:
    #     conda_prefix = which('conda')
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


def ygg_atexit():  # pragma: debug
    r"""Things to do at exit."""
    check_locks()
    check_threads()
    # # This causes a segfault in a C dependency
    # if not is_subprocess():
    #     check_sockets()
    # Python 3.4 no longer supported if using pip 9.0.0, but this
    # allows the code to work if somehow installed using an older
    # version of pip
    if sys.version_info[0:2] == (3, 4):  # pragma: no cover
        # Print empty line to ensure close
        print('', end='')
        sys.stdout.flush()


atexit.register(ygg_atexit)


def which(program):
    r"""Determine the path to an executable if it exists.

    Args:
        program (str): Name of program to locate or full path to program.

    Returns:
        str: Path to executable if it can be located. Otherwise, None.

    """
    if platform._is_win and (not program.endswith('.exe')):  # pragma: windows
        out = which(program + '.exe')
        if out is not None:
            return out
    return shutil.which(program)


def find_all(name, path):
    r"""Find all instances of a file with a given name within the directory
    tree starting at a given path.

    Args:
        name (str): Name of the file to be found (with the extension).
        path (str, None): Directory where search should start. If set to
            None on Windows, the current directory and PATH variable are
            searched.

    Returns:
        list: All instances of the specified file.

    """
    result = []
    try:
        if platform._is_win:  # pragma: windows
            if path is None:
                out = subprocess.check_output(["where", name],
                                              env=os.environ,
                                              stderr=subprocess.STDOUT)
            else:
                out = subprocess.check_output(["where", "/r", path, name],
                                              env=os.environ,
                                              stderr=subprocess.STDOUT)
        else:
            args = ["find", "-L", path, "-type", "f", "-name", name]
            pfind = subprocess.Popen(args, env=os.environ,
                                     stderr=subprocess.PIPE,
                                     stdout=subprocess.PIPE)
            (stdoutdata, stderrdata) = pfind.communicate()
            out = stdoutdata
            for l in stderrdata.splitlines():
                if b'Permission denied' not in l:
                    raise subprocess.CalledProcessError(pfind.returncode,
                                                        ' '.join(args),
                                                        output=stderrdata)
    except subprocess.CalledProcessError:
        out = ''
    if not out.isspace():
        result = sorted(out.splitlines())
    result = [os.path.normcase(os.path.normpath(bytes2str(m)))
              for m in result]
    return result


def locate_file(fname, environment_variable='PATH', directory_list=None):
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

    Returns:
        bool, str: Full path to the located file if it was located, False
            otherwise.

    """
    if isinstance(fname, list):
        out = False
        for ifname in fname:
            out = locate_file(ifname, environment_variable=environment_variable,
                              directory_list=directory_list)
            if out:
                break
        return out
    out = []
    if ((platform._is_win and (environment_variable == 'PATH')
         and (directory_list is None))):  # pragma: windows
        out += find_all(fname, None)
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
                out += find_all(fname, path)
    if not out:
        return False
    first = out[0]
    out = set(out)
    out.remove(first)
    if len(out) > 0:
        warnings.warn(("More than one (%d) match to %s:\n%s\n "
                       + "Using first match (%s)") %
                      (len(out) + 1, fname, pprint.pformat(out),
                       first), RuntimeWarning)
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


def remove_path(fpath, timer_class=None, timeout=None):
    r"""Delete a single file.

    Args:
        fpath (str): Full path to a file or directory that should be
            removed.
        timer_class (YggClass, optional): Class that should be used to
            generate a timer that is used to wait for file to be removed.
            Defaults to None and a new class instance will be created.
        timeout (float, optional): Time (in seconds) that should be
            waited before raising an error that a file cannot be removed.
            Defaults to None and will be set by the timer_class.

    Raises:
        RuntimeError: If the product cannot be removed.

    """
    if timer_class is None:
        timer_class = YggClass()
    if os.path.isdir(fpath):
        T = timer_class.start_timeout(t=timeout)
        while ((not T.is_out) and os.path.isdir(fpath)):
            try:
                shutil.rmtree(fpath)
            except BaseException:  # pragma: debug
                if os.path.isdir(fpath):
                    timer_class.sleep()
                if T.is_out:
                    raise
        timer_class.stop_timeout()
        if os.path.isdir(fpath):  # pragma: debug
            raise RuntimeError("Failed to remove directory: %s" % fpath)
    elif os.path.isfile(fpath):
        T = timer_class.start_timeout(t=timeout)
        while ((not T.is_out) and os.path.isfile(fpath)):
            try:
                os.remove(fpath)
            except BaseException:  # pragma: debug
                if os.path.isfile(fpath):
                    timer_class.sleep()
                if T.is_out:
                    raise
        timer_class.stop_timeout()
        if os.path.isfile(fpath):  # pragma: debug
            raise RuntimeError("Failed to remove file: %s" % fpath)


def get_supported_platforms():
    r"""Get a list of the platforms supported by yggdrasil.

    Returns:
        list: The name of platforms supported by yggdrasil.

    """
    return copy.deepcopy(platform._supported_platforms)


def get_supported_lang():
    r"""Get a list of the model programming languages that are supported
    by yggdrasil.

    Returns:
        list: The names of programming languages supported by yggdrasil.
    
    """
    from yggdrasil import schema
    s = schema.get_schema()
    out = s['model'].subtypes
    if 'c++' in out:
        out[out.index('c++')] = 'cpp'
    # if 'R' in out:
    #     out[out.index('R')] = 'r'
    if 'r' in out:
        out[out.index('r')] = 'R'
    return list(set(out))


def get_supported_type():
    r"""Get a list of the data types that are supported by yggdrasil.

    Returns:
        list: The names of data types supported by yggdrasil.

    """
    from yggdrasil.metaschema.datatypes import get_registered_types
    return list(get_registered_types().keys())


def get_supported_comm():
    r"""Get a list of the communication mechanisms supported by yggdrasil.

    Returns:
        list: The names of communication mechanisms supported by yggdrasil.

    """
    from yggdrasil import schema
    s = schema.get_schema()
    out = s['comm'].subtypes
    for k in ['CommBase', 'DefaultComm', 'default']:
        if k in out:
            out.remove(k)
    return list(set(out))


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


def get_installed_comm(language=None):
    r"""Get a list of the communication channel types that are supported by
    yggdrasil on the current machine. This checks the operating system,
    supporting libraries, and broker credentials. The order indicates the
    prefered order of use.

    Args:
        language (str, optional): Specific programming language that installed
            comms should be located for. Defaults to None and all languages
            supported on the current platform will be checked.

    Returns:
        list: The names of the the communication channel types supported on
            the current machine.

    """
    out = []
    all_comm = get_supported_comm()
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
    comm_list = get_installed_comm()
    if 'YGG_DEFAULT_COMM' in os.environ:
        _default_comm = os.environ['YGG_DEFAULT_COMM']
        if not is_comm_installed(_default_comm, language='any'):  # pragma: debug
            raise Exception('Unsupported default comm %s set by YGG_DEFAULT_COMM' % (
                            _default_comm))
    else:
        if len(comm_list) > 0:
            _default_comm = comm_list[0]
        else:  # pragma: windows
            # Locate comm that maximizes languages that can be run
            tally = {}
            for c in get_supported_comm():
                tally[c] = 0
                for l in get_supported_lang():
                    if is_comm_installed(c, language=l):
                        tally[c] += 1
            _default_comm = max(tally)
            if tally[_default_comm] == 0:  # pragma: debug
                raise Exception('Could not locate an installed comm.')
    if _default_comm.endswith('Comm'):
        _default_comm = import_component('comm', _default_comm)._commtype
    if _default_comm == 'rmq':  # pragma: debug
        raise NotImplementedError('RMQ cannot be the default comm because '
                                  + 'there is not an RMQ C interface.')
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
                print("calling interrupt", pid)
                os.kill(pid, sigmap[signum])
                # busy wait because we can't block in the main
                # thread, else the signal handler can't execute.
                while not event.is_set():
                    pass
                print("after interrupt")
            finally:
                signal.signal(signum, handler)
                print("in finally")
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
    _safe_lists = {'math': ['acos', 'asin', 'atan', 'atan2', 'ceil', 'cos',
                            'cosh', 'degrees', 'e', 'exp', 'fabs', 'floor', 'fmod',
                            'frexp', 'hypot', 'ldexp', 'log', 'log10', 'modf', 'pi',
                            'pow', 'radians', 'sin', 'sinh', 'sqrt', 'tan', 'tanh'],
                   'builtins': ['abs', 'any', 'bool', 'bytes', 'float', 'int', 'len',
                                'list', 'map', 'max', 'min', 'repr', 'set', 'str',
                                'sum', 'tuple', 'type'],
                   'numpy': ['array', 'int8', 'int16', 'int32', 'int64',
                             'uint8', 'uint16', 'uint32', 'uint64',
                             'float16', 'float32', 'float64'],
                   'yggdrasil.units': ['get_data', 'add_units'],
                   'unyt.array': ['unyt_quantity', 'unyt_array']}
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
                    master_fd, slave_fd = pty.openpty()
                    kwargs.setdefault('stdin', slave_fd)

                kwargs.setdefault('preexec_fn', os.setpgrp)
        # if platform._is_win:  # pragma: windows
        #     kwargs.setdefault('universal_newlines', True)
        super(YggPopen, self).__init__(cmd_args, **kwargs)

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


def print_encoded(msg, *args, **kwargs):
    r"""Print bytes to stdout, encoding if possible.

    Args:
        msg (str, bytes): Message to print.
        *args: Additional arguments are passed to print.
        **kwargs: Additional keyword arguments are passed to print.


    """
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

    @property
    def elapsed(self):
        r"""float: Total time that has elapsed since the start."""
        return time.perf_counter() - self.start_time
    
    @property
    def is_out(self):
        r"""bool: True if there is not any time remaining. False otherwise."""
        if self.max_time is False:
            return False
        return (self.elapsed > self.max_time)


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


class YggClass(ComponentBase, logging.LoggerAdapter):
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
        # self.logger = logging.getLogger(self.__module__)
        # self.logger.basicConfig(
        #     format=("%(levelname)s:%(module)s" +
        #             # "(%s)" % self.name +
        #             ".%(funcName)s[%(lineno)d]:%(message)s"))
        self._old_loglevel = None
        self._old_encoding = None
        self.debug_flag = False
        self._ygg_class = str(self.__class__).split("'")[1].split('.')[-1]
        # Call super class, adding in schema properties
        for k in self._base_defaults:
            if k in self._schema_properties:
                kwargs[k] = getattr(self, k)
        super(YggClass, self).__init__(**kwargs)
        logging.LoggerAdapter.__init__(self, logging.getLogger(self.__module__), {})

    def __deepcopy__(self, memo):
        r"""Don't deep copy since threads cannot be copied."""
        return self

    @property
    def name(self):
        r"""str: Name of the class object."""
        return self._name

    @property
    def ygg_class(self):
        r"""str: Name of the class."""
        return self._ygg_class

    def language_info(self, languages):
        r"""Only do info debug message if the language is one of those specified."""
        if not isinstance(languages, (list, tuple)):
            languages = [languages]
        languages = [l.lower() for l in languages]
        if get_subprocess_language().lower() in languages:  # pragma: debug
            return self.info
        else:
            return self.dummy_log

    @property
    def interface_info(self):
        r"""Only do info debug message if is interface."""
        if is_subprocess():  # pragma: debug
            return self.info
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

    def process(self, msg, kwargs):
        r"""Process logging message."""
        if _stack_in_log:  # pragma: no cover
            stack = inspect.stack()
            the_class = os.path.splitext(os.path.basename(
                stack[2][0].f_globals["__file__"]))[0]
            the_line = stack[2][2]
            the_func = stack[2][3]
            prefix = '%s(%s).%s[%d]' % (the_class, self.name, the_func, the_line)
        else:
            prefix = '%s(%s)' % (self.ygg_class, self.name)
        new_msg = '%s: %s' % (prefix, self.as_str(msg))
        return new_msg, kwargs

    def display(self, msg='', *args, **kwargs):
        r"""Print a message, no log."""
        msg, kwargs = self.process(msg, kwargs)
        print(msg % args)

    def verbose_debug(self, *args, **kwargs):
        r"""Log a verbose debug level message."""
        return self.log(9, *args, **kwargs)
        
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
            return self.debug
        else:
            return self.dummy_log

    @property
    def special_debug(self):
        r"""Log debug level message contingent of supression flag."""
        if not self.suppress_special_debug:
            return self.debug
        else:
            return self.dummy_log

    @property
    def error(self):
        r"""Log an error level message."""
        self.errors.append('ERROR')
        return super(YggClass, self).error

    @property
    def exception(self):
        r"""Log an exception level message."""
        exc_info = sys.exc_info()
        if exc_info is not None and exc_info != (None, None, None):
            self.errors.append('ERROR')
            return super(YggClass, self).exception
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

    def printStatus(self):
        r"""Print the class status."""
        self.info('%s(%s): state:', self.__module__, self.name)

    def _task_with_output(self, func, *args, **kwargs):
        self.sched_out = func(*args, **kwargs)

    def sched_task(self, t, func, args=None, kwargs=None, store_output=False):
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
        tobj.start()

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
            key = '%s(%s).%s.%s' % (cls, self.name, fcn,
                                    threading.current_thread().name)
        else:
            key = '%s(%s).%s' % (str(self.__class__).split("'")[1], self.name,
                                 threading.current_thread().name)
        if key_suffix is not None:
            key += key_suffix
        return key

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
                self.error("Timeout for %s at %5.2f/%5.2f s" % (
                    key, t.elapsed, t.max_time))
        del self._timeouts[key]
        

class YggThread(threading.Thread, YggClass):
    r"""Thread for Ygg that tracks when the thread is started and joined.

    Attributes:
        lock (threading.RLock): Lock for accessing the sockets from multiple
            threads.
        start_event (threading.Event): Event indicating that the thread was
            started.
        terminate_event (threading.Event): Event indicating that the thread
            should be terminated. The target must exit when this is set.

    """
    def __init__(self, name=None, target=None, args=(), kwargs=None,
                 daemon=False, group=None, **ygg_kwargs):
        global _lock_registry
        if kwargs is None:
            kwargs = {}
        if (target is not None) and ('target' in self._schema_properties):
            ygg_kwargs['target'] = target
            target = None
        thread_kwargs = dict(name=name, target=target, group=group,
                             args=args, kwargs=kwargs)
        super(YggThread, self).__init__(**thread_kwargs)
        YggClass.__init__(self, self.name, **ygg_kwargs)
        self._ygg_target = target
        self._ygg_args = args
        self._ygg_kwargs = kwargs
        self.debug('')
        self.lock = threading.RLock()
        self.start_event = threading.Event()
        self.terminate_event = threading.Event()
        self.start_flag = False
        self.terminate_flag = False
        self._cleanup_called = False
        self._calling_thread = None
        if daemon:  # pragma: debug
            self.setDaemon(True)
            self.daemon = True
        _thread_registry[self.name] = self
        _lock_registry[self.name] = self.lock
        atexit.register(self.atexit)

    @property
    def main_terminated(self):
        r"""bool: True if the main thread has terminated."""
        return (not _main_thread.is_alive())
        # return (not self._calling_thread.is_alive())

    def set_started_flag(self):
        r"""Set the started flag for the thread to True."""
        # self.start_event.set()
        self.start_flag = True

    def set_terminated_flag(self):
        r"""Set the terminated flag for the thread to True."""
        # self.terminate_event.set()
        self.terminate_flag = True

    def unset_started_flag(self):  # pragma: debug
        r"""Set the started flag for the thread to False."""
        # self.start_event.clear()
        self.start_flag = False

    def unset_terminated_flag(self):  # pragma: debug
        r"""Set the terminated flag for the thread to False."""
        # self.terminate_event.clear()
        self.terminated_flag = False

    @property
    def was_started(self):
        r"""bool: True if the thread was started. False otherwise."""
        # return self.start_event.is_set()
        return self.start_flag

    @property
    def was_terminated(self):
        r"""bool: True if the thread was terminated. False otherwise."""
        # return self.terminate_event.is_set()
        return self.terminate_flag

    def start(self, *args, **kwargs):
        r"""Start thread and print info."""
        self.debug('')
        if not self.was_terminated:
            self.set_started_flag()
            self.before_start()
        super(YggThread, self).start(*args, **kwargs)
        self._calling_thread = threading.current_thread()
        # print("Thread = %s, Called by %s" % (self.name, self._calling_thread.name))

    def run(self, *args, **kwargs):
        r"""Continue running until terminate event set."""
        self.debug("Starting method")
        try:
            super(YggThread, self).run(*args, **kwargs)
        except BaseException:  # pragma: debug
            self.exception("THREAD ERROR")
        finally:
            for k in ['_ygg_target', '_ygg_args', '_ygg_kwargs']:
                if hasattr(self, k):
                    delattr(self, k)

    def before_start(self):
        r"""Actions to perform on the main thread before starting the thread."""
        self.debug('')

    def cleanup(self):
        r"""Actions to perform to clean up the thread after it has stopped."""
        self._cleanup_called = True

    def wait(self, timeout=None, key=None):
        r"""Wait until thread finish to return using sleeps rather than
        blocking.

        Args:
            timeout (float, optional): Maximum time that should be waited for
                the driver to finish. Defaults to None and is infinite.
            key (str, optional): Key that should be used to register the timeout.
                Defaults to None and is set based on the stack trace.

        """
        T = self.start_timeout(timeout, key_level=1, key=key)
        while self.is_alive() and not T.is_out:
            self.verbose_debug('Waiting for thread to finish...')
            self.sleep()
        self.stop_timeout(key_level=1, key=key)

    def terminate(self, no_wait=False):
        r"""Set the terminate event and wait for the thread to stop.

        Args:
            no_wait (bool, optional): If True, terminate will not block until
                the thread stops. Defaults to False and blocks.

        Raises:
            AssertionError: If no_wait is False and the thread has not stopped
                after the timeout.

        """
        self.debug('')
        with self.lock:
            if self.was_terminated:  # pragma: debug
                self.debug('Driver already terminated.')
                return
            self.set_terminated_flag()
        if not no_wait:
            # if self.is_alive():
            #     self.join(self.timeout)
            self.wait(timeout=self.timeout)
            assert(not self.is_alive())

    def atexit(self):  # pragma: debug
        r"""Actions performed when python exits."""
        # self.debug('is_alive = %s', self.is_alive())
        if self.is_alive():
            self.info('Thread alive at exit')
            if not self._cleanup_called:
                self.cleanup()


class YggThreadLoop(YggThread):
    r"""Thread that will run a loop until the terminate event is called."""
    def __init__(self, *args, **kwargs):
        super(YggThreadLoop, self).__init__(*args, **kwargs)
        self._1st_main_terminated = False
        self.break_flag = False
        self.loop_event = threading.Event()
        self.loop_flag = False

    def on_main_terminated(self, dont_break=False):  # pragma: debug
        r"""Actions performed when 1st main terminated.

        Args:
            dont_break (bool, optional): If True, the break flag won't be set.
                Defaults to False.

        """
        self._1st_main_terminated = True
        if not dont_break:
            self.set_break_flag()

    def set_break_flag(self):
        r"""Set the break flag for the thread to True."""
        self.break_flag = True

    def unset_break_flag(self):  # pragma: debug
        r"""Set the break flag for the thread to False."""
        self.break_flag = False

    @property
    def was_break(self):
        r"""bool: True if the break flag was set."""
        return self.break_flag

    def set_loop_flag(self):
        r"""Set the loop flag for the thread to True."""
        # self.loop_event.set()
        self.loop_flag = True

    def unset_loop_flag(self):  # pragma: debug
        r"""Set the loop flag for the thread to False."""
        # self.loop_event.clear()
        self.loop_flag = False

    @property
    def was_loop(self):
        r"""bool: True if the thread was loop. False otherwise."""
        # return self.loop_event.is_set()
        return self.loop_flag

    def wait_for_loop(self, timeout=None, key=None):
        r"""Wait until thread enters loop to return using sleeps rather than
        blocking.

        Args:
            timeout (float, optional): Maximum time that should be waited for
                the thread to enter loop. Defaults to None and is infinite.
            key (str, optional): Key that should be used to register the timeout.
                Defaults to None and is set based on the stack trace.

        """
        T = self.start_timeout(timeout, key_level=1, key=key)
        while (self.is_alive() and (not self.was_loop)
               and (not T.is_out)):  # pragma: debug
            self.verbose_debug('Waiting for thread to enter loop...')
            self.sleep()
        self.stop_timeout(key_level=1, key=key)

    def before_loop(self):
        r"""Actions performed before the loop."""
        self.debug('')

    def run_loop(self, *args, **kwargs):
        r"""Actions performed on each loop iteration."""
        if self._ygg_target:
            self._ygg_target(*self._ygg_args, **self._ygg_kwargs)
        else:
            self.set_break_flag()

    def after_loop(self):
        r"""Actions performed after the loop."""
        self.debug('')

    def run(self, *args, **kwargs):
        r"""Continue running until terminate event set."""
        self.debug("Starting loop")
        try:
            self.before_loop()
            if (not self.was_break):
                self.set_loop_flag()
            while (not self.was_break):
                if ((self.main_terminated
                     and (not self._1st_main_terminated))):  # pragma: debug
                    self.on_main_terminated()
                else:
                    self.run_loop()
            self.set_break_flag()
        except BaseException:  # pragma: debug
            self.exception("THREAD ERROR")
            self.set_break_flag()
        finally:
            for k in ['_ygg_target', '_ygg_args', '_ygg_kwargs']:
                if hasattr(self, k):
                    delattr(self, k)
        try:
            self.after_loop()
        except BaseException:  # pragma: debug
            self.exception("AFTER LOOP ERROR")

    def terminate(self, *args, **kwargs):
        r"""Also set break flag."""
        self.set_break_flag()
        super(YggThreadLoop, self).terminate(*args, **kwargs)
