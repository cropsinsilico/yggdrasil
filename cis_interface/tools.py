"""This modules offers various tools."""
from __future__ import print_function
import threading
import logging
import os
import sys
import inspect
import time
import signal
import yaml
import pystache
import warnings
from cis_interface.backwards import sio
import subprocess
from cis_interface import platform
from cis_interface import backwards
from cis_interface.config import cis_cfg, cfg_logging


def locate_path(fname, basedir=os.path.abspath(os.sep)):
    r"""Find the full path to a file using where on Windows."""
    try:
        if platform._is_win:
            out = subprocess.check_output(["dir", fname, "/s/b"], shell=True,
                                          cwd=basedir)
            # out = subprocess.check_output(["where", fname])
        else:
            # find . -name "filetofind" 2>&1 | grep -v 'permission denied'
            out = subprocess.check_output(["find", basedir, "-name", fname])  # ,
            # "2>&1", "|", "grep", "-v", "'permission denied'"])
            # out = subprocess.check_output(["locate", "-b", "--regex",
            #                                "^%s" % fname])
    except subprocess.CalledProcessError:
        return False
    if out.isspace():
        return False
    out = out.decode('utf-8').splitlines()
    # out = backwards.bytes2unicode(out.splitlines()[0])
    return out


def is_ipc_installed():
    r"""Determine if the IPC libraries are installed.

    Returns:
        bool: True if the IPC libraries are installed, False otherwise.

    """
    return (platform._is_linux or platform._is_osx)


def is_zmq_installed():
    r"""Determine if the libczmq & libzmq libraries are installed.

    Returns:
        bool: True if both libraries are installed, False otherwise.

    """
    # Check existence of files
    # check_files = ['zmq.h', 'czmq.h']
    # if platform._is_win:
    #     check_files += ['zmq.lib', 'czmq.lib']
    #     check_files += ['libzmq-*dll', 'libczmq.dll']
    # for f in check_files:
    #     if not locate_path(f):
    #         warnings.warn("Could not locate ZeroMQ headers/libraries on PATH")
    #         return False
    # Check existence of config paths for windows
    if platform._is_win:
        opts = ['libzmq_include', 'libzmq_static', 'libzmq_dynamic',
                'czmq_include', 'czmq_static', 'czmq_dynamic']
        for o in opts:
            if not cis_cfg.get('windows', o, None):
                warnings.warn("Config option %s not set." % o)
                return False
        return True
    else:
        process = subprocess.Popen(['gcc', '-lzmq', '-lczmq'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        outs, errs = process.communicate()
        # Python 3
        # try:
        #     outs, errs = process.communicate(timeout=15)
        # except subprocess.TimeoutExpired:
        #     process.kill()
        #     outs, errs = process.communicate()
        return (backwards.unicode2bytes('zmq') not in errs)


_ipc_installed = is_ipc_installed()
_zmq_installed = is_zmq_installed()
# OS X limit is 2kb
if _zmq_installed:
    CIS_MSG_MAX = 2**20
else:
    CIS_MSG_MAX = 1024 * 2
CIS_MSG_EOF = backwards.unicode2bytes("EOF!!!")
CIS_MSG_BUF = 1024 * 2

PSI_MSG_MAX = CIS_MSG_MAX
PSI_MSG_EOF = CIS_MSG_EOF
PSI_MSG_BUF = CIS_MSG_BUF


# https://stackoverflow.com/questions/35772001/
# how-to-handle-the-signal-in-python-on-windows-machine
def kill(pid, signum):
    r"""Kill process by mapping signal number."""
    if platform._is_win:
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
        if (((signum in sigmap) and (thread.name == 'MainThread') and
             callable(handler) and (pid == 0))):
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


def parse_yaml(fname):
    r"""Parse a yaml file defining a run.

    Args:
        fname (str): Path to the yaml file.

    Returns:
        dict: Contents of yaml file.

    """
    # Open file and parse yaml
    with open(fname, 'r') as f:
        # Mustache replace vars
        yamlparsed = f.read()
        yamlparsed = pystache.render(
            sio.StringIO(yamlparsed).getvalue(), dict(os.environ))
        yamlparsed = yaml.safe_load(yamlparsed)
    return yamlparsed

    
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


def popen_nobuffer(args, forward_signals=True, **kwargs):
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
        subprocess.Process: Process that was started.

    """
    # stdbuf only for linux
    if platform._is_linux:
        stdbuf_args = ['stdbuf', '-o0', '-e0']
        if isinstance(args, str):
            args = ' '.join(stdbuf_args + [args])
        else:
            args = stdbuf_args + args
    kwargs.setdefault('bufsize', 0)
    kwargs.setdefault('stdout', subprocess.PIPE)
    kwargs.setdefault('stderr', subprocess.STDOUT)
    if not forward_signals:
        if platform._is_win:
            kwargs.setdefault('preexec_fn', None)
            kwargs.setdefault('creationflags', subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            kwargs.setdefault('preexec_fn', os.setpgrp)
    # if platform._is_win:
    #     kwargs.setdefault('universal_newlines', True)
    out = subprocess.Popen(args, **kwargs)
    return out


def print_encoded(msg, *args, **kwargs):
    r"""Print bytes to stdout, encoding if possible.

    Args:
        msg (str, bytes): Message to print.
        *args: Additional arguments are passed to print.
        **kwargs: Additional keyword arguments are passed to print.


    """
    try:
        print(backwards.bytes2unicode(msg), *args, **kwargs)
    except UnicodeEncodeError:  # pragma: debug
        logging.debug("sys.stdout.encoding = %s, cannot print unicode",
                      sys.stdout.encoding)
        kwargs.pop('end', None)
        try:
            print(msg, *args, **kwargs)
        except UnicodeEncodeError:  # pragma: debug
            print(backwards.unicode2bytes(msg), *args, **kwargs)


class TimeOut(object):
    r"""Class for checking if a period of time has been elapsed.

    Args:
        max_time (float, bbol): Maximum period of time that should elapse before
            'is_out' returns True. If False, 'is_out' will never return True.
            Providing 0 indicates that 'is_out' should immediately return True.

    Attributes:
        max_time (float): Maximum period of time that should elapsed before
            'is_out' returns True.
        start_time (float): Result of time.time() at start.

    """

    def __init__(self, max_time):
        self.max_time = max_time
        self.start_time = backwards.clock_time()

    @property
    def elapsed(self):
        r"""float: Total time that has elapsed since the start."""
        return backwards.clock_time() - self.start_time
    
    @property
    def is_out(self):
        r"""bool: True if there is not any time remaining. False otherwise."""
        if self.max_time is False:
            return False
        return (self.elapsed > self.max_time)


class CisClass(object):
    r"""Base class for CiS classes.

    Args:
        name (str): Class name.
        workingDir (str, optional): Working directory. If not provided, the
            current working directory is used.
        timeout (float, optional): Maximum time (in seconds) that should be
            spent waiting on a process. Defaults to 60.
        sleeptime (float, optional): Time that class should sleep for when
            sleep is called. Defaults to 0.01.
        **kwargs: Additional keyword arguments are assigned to the extra_kwargs
            dictionary.

    Attributes:
        name (str): Class name.
        sleeptime (float): Time that class should sleep for when sleep called.
        longsleep (float): Time that the class will sleep for when waiting for
            longer tasks to complete (10x longer than sleeptime).
        timeout (float): Maximum time that should be spent waiting on a process.
        workingDir (str): Working directory.
        errors (list): List of errors.
        extra_kwargs (dict): Keyword arguments that were not parsed.
        sched_out (obj): Output from the last scheduled task with output.
        logger (logging.Logger): Logger object for this object.
        suppress_special_debug (bool): If True, special_debug log messages
            are suppressed.

    """
    def __init__(self, name, workingDir=None, timeout=60.0, sleeptime=0.01,
                 **kwargs):
        self.name = name
        self.sleeptime = sleeptime
        self.longsleep = self.sleeptime * 10
        self.timeout = timeout
        self._timeouts = {}
        # Set defaults
        if workingDir is None:
            workingDir = os.getcwd()
        # Assign things
        self.workingDir = workingDir
        self.errors = []
        self.extra_kwargs = kwargs
        self.sched_out = None
        self.suppress_special_debug = False
        self.logger = logging.getLogger(self.__module__)
        self._old_loglevel = None
        self.debug_flag = False

    def debug_log(self):  # pragma: debug
        r"""Turn on debugging."""
        self._old_loglevel = cis_cfg.get('debug', 'psi')
        cis_cfg.set('debug', 'psi', 'DEBUG')
        cfg_logging()

    def reset_log(self):  # pragma: debug
        r"""Resetting logging to prior value."""
        if self._old_loglevel is not None:
            cis_cfg.set('debug', 'psi', self._old_loglevel)
            cfg_logging()
            self._old_loglevel = None

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
        self.logger.error('%s(%s): state:', self.__module__, self.name)

    def _task_with_output(self, func, *args, **kwargs):
        self.sched_out = func(*args, **kwargs)

    def sched_task(self, t, func, args=[], kwargs={}, store_output=False):
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
        self.sched_out = None
        if store_output:
            tobj = threading.Timer(t, self._task_with_output,
                                   args=[func] + args, kwargs=kwargs)
        else:
            tobj = threading.Timer(t, func, args=args, kwargs=kwargs)
        tobj.start()

    @property
    def logger_prefix(self):
        r"""Prefix to add to logger messages."""
        stack = inspect.stack()
        the_class = os.path.splitext(os.path.basename(
            stack[2][0].f_globals["__file__"]))[0]
        the_line = stack[2][2]
        the_func = stack[2][3]
        return '%s(%s).%s[%d]: ' % (the_class, self.name, the_func, the_line)

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
            
    def sleep(self, t=None):
        r"""Have the class sleep for some period of time.

        Args:
            t (float, optional): Time that class should sleep for. If not
                provided, the attribute 'sleeptime' is used.

        """
        if t is None:
            t = self.sleeptime
        time.sleep(t)

    @property
    def timeout_key(self):
        r"""str: Key identifying calling object and method."""
        stack = inspect.stack()
        fcn = stack[2][3]
        cls = os.path.splitext(os.path.basename(stack[2][1]))[0]
        key = '%s(%s).%s' % (cls, self.name, fcn)
        return key

    def start_timeout(self, t=None, key=None):
        r"""Start a timeout for the calling function/method.

        Args:
            t (float, optional): Maximum time that the calling function should
                wait before timeing out. If not provided, the attribute
                'timeout' is used.
            key (str, optional): Key that should be associated with the timeout
                that is created. Defaults to None and is set by the calling
                class and function/method (See `timeout_key`).

        Raises:
            KeyError: If the key already exists.

        """
        if t is None:
            t = self.timeout
        if key is None:
            key = self.timeout_key
        if key in self._timeouts:
            raise KeyError("Timeout already registered for %s" % key)
        self._timeouts[key] = TimeOut(t)
        return self._timeouts[key]

    def check_timeout(self, key=None):
        r"""Check timeout for the calling function/method.

        Args:
            key (str, optional): Key for timeout that should be checked.
                Defaults to None and is set by the calling class and
                function/method (See `timeout_key`).

        Raises:
            KeyError: If there is not a timeout registered for the specified
                key.

        """
        if key is None:
            key = self.timeout_key
        if key not in self._timeouts:
            raise KeyError("No timeout registered for %s" % key)
        t = self._timeouts[key]
        return t.is_out
        
    def stop_timeout(self, key=None):
        r"""Stop a timeout for the calling function method.

        Args:
            key (str, optional): Key for timeout that should be stopped.
                Defaults to None and is set by the calling class and
                function/method (See `timeout_key`).

        Raises:
            KeyError: If there is not a timeout registered for the specified
                key.

        """
        if key is None:
            key = self.timeout_key
        if key not in self._timeouts:
            raise KeyError("No timeout registered for %s" % key)
        t = self._timeouts[key]
        if t.is_out and t.max_time > 0:
            self.error("Timeout for %s at %5.2f s" % (key, t.elapsed))
            print("Stopped %s at %f/%f" % (key, t.elapsed, t.max_time))
        del self._timeouts[key]

    def display(self, fmt_str='', *args):
        r"""Log a message at level 1000 that is prepended with the class
        and name. These messages will always be printed.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        print(self.logger_prefix + self.as_str(fmt_str) % args)

    def info(self, fmt_str='', *args):
        r"""Log an info message that is prepended with the class and name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        self.logger.info(self.logger_prefix + self.as_str(fmt_str), *args)

    def debug(self, fmt_str='', *args):
        r"""Log a debug message that is prepended with the class and name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        self.logger.debug(self.logger_prefix + self.as_str(fmt_str), *args)

    def special_debug(self, fmt_str='', *args):
        r"""Log a debug message that is prepended with the class and name, but
        only if self.suppress_special_debug is not True.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        if not self.suppress_special_debug:
            self.logger.debug(self.logger_prefix + self.as_str(fmt_str), *args)

    def verbose_debug(self, fmt_str='', *args):
        r"""Log a verbose debug message that is prepended with the class and name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        self.logger.log(9, self.logger_prefix + self.as_str(fmt_str), *args)
        
    def critical(self, fmt_str='', *args):
        r"""Log a critical message that is prepended with the class and name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        self.logger.critical(self.logger_prefix + self.as_str(fmt_str), *args)

    def warn(self, fmt_str='', *args):
        r"""Log a warning message that is prepended with the class and name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        self.logger.warn(self.logger_prefix + self.as_str(fmt_str), *args)

    def error(self, fmt_str='', *args):
        r"""Log an error message that is prepended with the class and name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        fmt_str = self.as_str(fmt_str)
        self.logger.error(self.logger_prefix + fmt_str, *args)
        self.errors.append((self.logger_prefix + fmt_str) % args)

    def exception(self, fmt_str='', *args):
        r"""Log an exception message that is prepended with the class name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        fmt_str = self.as_str(fmt_str)
        exc_info = sys.exc_info()
        if exc_info is not None and exc_info != (None, None, None):
            self.logger.exception(self.logger_prefix + fmt_str, *args)
        else:
            self.logger.error(self.logger_prefix + fmt_str, *args)
        self.errors.append((self.logger_prefix + fmt_str) % args)

    def raise_error(self, e):
        r"""Raise an exception, logging it first.

        Args:
            e (Exception): Exception to raise.

        Raises:
            The provided exception.

        """
        self.errors.append(repr(e))
        raise e
