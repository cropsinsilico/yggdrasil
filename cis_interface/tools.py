"""This modules offers various tools."""
from __future__ import print_function
import threading
import logging
import os
import sys
import inspect
import time
import signal
import warnings
import atexit
import uuid as uuid_gen
import subprocess
from cis_interface import platform
from cis_interface import backwards
from cis_interface.config import cis_cfg, cfg_logging


_stack_in_log = False
_stack_in_timeout = False
if ((logging.getLogger("cis_interface").getEffectiveLevel() <=
     logging.DEBUG)):  # pragma: debug
    _stack_in_log = False
    _stack_in_timeout = True
_thread_registry = {}
_lock_registry = {}
try:
    _main_thread = threading.main_thread()
except AttributeError:
    _main_thread = None
    for i in threading.enumerate():
        if (i.name == "MainThread"):
            _main_thread = i
            break
    if _main_thread is None:  # pragma: debug
        raise RuntimeError("Could not located MainThread")


def check_threads():  # pragma: debug
    r"""Check for threads that are still running."""
    global _thread_registry
    # logging.info("Checking %d threads" % len(_thread_registry))
    for k, v in _thread_registry.items():
        if v.is_alive():
            logging.error("Thread is alive: %s" % k)
    if threading.active_count() > 1:
        logging.info("%d threads running" % threading.active_count())
        for t in threading.enumerate():
            logging.info("%s thread running" % t.name)


def check_locks():  # pragma: debug
    r"""Check for locks in lock registry that are locked."""
    global _lock_registry
    # logging.info("Checking %d locks" % len(_lock_registry))
    for k, v in _lock_registry.items():
        res = v.acquire(False)
        if res:
            v.release()
        else:
            logging.error("Lock could not be acquired: %s" % k)


def check_sockets():  # pragma: debug
    r"""Check registered sockets."""
    from cis_interface.communication import cleanup_comms
    count = cleanup_comms('ZMQComm')
    if count > 0:
        logging.info("%d sockets closed." % count)


def cis_atexit():  # pragma: debug
    r"""Things to do at exit."""
    check_locks()
    check_threads()
    if not os.environ.get('CIS_SUBPROCESS', False):
        check_sockets()
    if backwards.PY34:
        # Print empty line to ensure close
        print('', end='')
        sys.stdout.flush()


atexit.register(cis_atexit)


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
    out = out.decode('utf-8').splitlines()
    # out = backwards.bytes2unicode(out.splitlines()[0])
    return out


def is_ipc_installed():
    r"""Determine if the IPC libraries are installed.

    Returns:
        bool: True if the IPC libraries are installed, False otherwise.

    """
    return (platform._is_linux or platform._is_osx)


def is_zmq_installed(check_c=True):
    r"""Determine if the libczmq & libzmq libraries are installed.

    Returns:
        bool: True if both libraries are installed, False otherwise.

    """
    # Check existence of zmq python package
    try:
        import zmq
    except ImportError:  # pragma: debug
        return False
    assert(zmq)
    if not check_c:  # pragma: windows
        return True
    # Check existence of config paths for windows
    if platform._is_win:  # pragma: windows
        opts = ['libzmq_include', 'libzmq_static',  # 'libzmq_dynamic',
                'czmq_include', 'czmq_static']  # , 'czmq_dynamic']
        for o in opts:
            if not cis_cfg.get('windows', o, None):  # pragma: debug
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
_zmq_installed_c = _zmq_installed
if not (_ipc_installed or _zmq_installed):  # pragma: windows
    if is_zmq_installed(check_c=False):
        logging.warning(("ZeroMQ C library not installed, but the Python package is. " +
                         "Running C and C++ models will be disabled."))
        _zmq_installed_c = False
        _zmq_installed = True
    else:  # pragma: debug
        raise Exception('Neither ZMQ or IPC installed.')
_c_library_avail = (_ipc_installed or _zmq_installed_c)

CIS_MSG_EOF = backwards.unicode2bytes("EOF!!!")
CIS_MSG_BUF = 1024 * 2


def get_default_comm():
    r"""Get the default comm that should be used for message passing."""
    if 'CIS_DEFAULT_COMM' in os.environ:
        _default_comm = os.environ['CIS_DEFAULT_COMM']
        if _default_comm not in ['ZMQComm', 'IPCComm', 'RMQComm']:  # pragma: debug
            raise Exception('Unrecognized default comm %s set by CIS_DEFAULT_COMM' % (
                            _default_comm))
    elif _zmq_installed_c:
        _default_comm = 'ZMQComm'
    elif _ipc_installed:
        _default_comm = 'IPCComm'
    elif _zmq_installed:  # pragma: windows
        _default_comm = 'ZMQComm'
    else:  # pragma: debug
        raise Exception('Neither ZMQ nor IPC installed.')
    return _default_comm


def get_CIS_MSG_MAX():
    r"""Get the maximum message size for the default comm."""
    _default_comm = get_default_comm()
    if _default_comm == 'IPCComm':
        # OS X limit is 2kb
        out = 1024 * 2
    else:
        out = 2**20
    return out


CIS_MSG_MAX = get_CIS_MSG_MAX()


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
        if (((signum in sigmap) and (thread.name == 'MainThread') and
             callable(handler) and ((pid == os.getpid()) or (pid == 0)))):
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
    if platform._is_win and backwards.PY2:  # pragma: windows
        while True:
            try:
                t = time.time()
                time.sleep(interval)
            except IOError as e:  # pragma: debug
                import errno
                if e.errno != errno.EINTR:
                    raise
            # except InterruptedError:  # pragma: debug
            #     import errno
            #     print(e.errno)
            #     print(e)
            interval -= time.time() - t
            if interval <= 0:
                break
    else:
        time.sleep(interval)


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


class CisPopen(subprocess.Popen):
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
    def __init__(self, cmd_args, forward_signals=True, **kwargs):
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
        if not forward_signals:
            if platform._is_win:  # pragma: windows
                kwargs.setdefault('preexec_fn', None)
                kwargs.setdefault('creationflags', subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                kwargs.setdefault('preexec_fn', os.setpgrp)
        # if platform._is_win:  # pragma: windows
        #     kwargs.setdefault('universal_newlines', True)
        super(CisPopen, self).__init__(cmd_args, **kwargs)

    def kill(self, *args, **kwargs):
        r"""On windows using CTRL_BREAK_EVENT to kill the process."""
        if platform._is_win:  # pragma: windows
            self.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            super(CisPopen, self).kill(*args, **kwargs)


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
        CisPopen: Process that was started.

    """
    return CisPopen(*args, **kwargs)


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
        self.start_time = backwards.clock_time()
        self.key = key

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


# def single_use_method(func):
#     r"""Decorator for marking functions that should only be called once."""
#     def wrapper(*args, **kwargs):
#         if getattr(func, '_single_use_method_called', False):
#             logging.info("METHOD %s ALREADY CALLED" % func)
#             return
#         else:
#             func._single_use_method_called = True
#             return func(*args, **kwargs)
#     return wrapper


class CisClass(logging.LoggerAdapter):
    r"""Base class for CiS classes.

    Args:
        name (str): Class name.
        uuid (str, optional): Unique ID for this instance. Defaults to None
            and is assigned.
        working_dir (str, optional): Working directory. If not provided, the
            current working directory is used.
        timeout (float, optional): Maximum time (in seconds) that should be
            spent waiting on a process. Defaults to 60.
        sleeptime (float, optional): Time that class should sleep for when
            sleep is called. Defaults to 0.01.
        **kwargs: Additional keyword arguments are assigned to the extra_kwargs
            dictionary.

    Attributes:
        name (str): Class name.
        uuid (str): Unique ID for this instance.
        sleeptime (float): Time that class should sleep for when sleep called.
        longsleep (float): Time that the class will sleep for when waiting for
            longer tasks to complete (10x longer than sleeptime).
        timeout (float): Maximum time that should be spent waiting on a process.
        working_dir (str): Working directory.
        errors (list): List of errors.
        extra_kwargs (dict): Keyword arguments that were not parsed.
        sched_out (obj): Output from the last scheduled task with output.
        logger (logging.Logger): Logger object for this object.
        suppress_special_debug (bool): If True, special_debug log messages
            are suppressed.

    """
    def __init__(self, name, uuid=None, working_dir=None,
                 timeout=60.0, sleeptime=0.01, **kwargs):
        self._name = name
        if uuid is None:
            uuid = str(uuid_gen.uuid4())
        self.uuid = uuid
        self.sleeptime = sleeptime
        self.longsleep = self.sleeptime * 10
        self.timeout = timeout
        self._timeouts = {}
        # Set defaults
        if working_dir is None:
            working_dir = os.getcwd()
        # Assign things
        self.working_dir = working_dir
        self.errors = []
        self.extra_kwargs = kwargs
        self.sched_out = None
        self.suppress_special_debug = False
        # self.logger = logging.getLogger(self.__module__)
        # self.logger.basicConfig(
        #     format=("%(levelname)s:%(module)s" +
        #             # "(%s)" % self.name +
        #             ".%(funcName)s[%(lineno)d]:%(message)s"))
        self._old_loglevel = None
        self._old_encoding = None
        self.debug_flag = False
        class_name = str(self.__class__).split("'")[1].split('.')[-1]
        super(CisClass, self).__init__(logging.getLogger(self.__module__),
                                       {'cis_name': self.name,
                                        'cis_class': class_name})

    @property
    def name(self):
        r"""Name of the class object."""
        return self._name

    def debug_log(self):  # pragma: debug
        r"""Turn on debugging."""
        self._old_loglevel = cis_cfg.get('debug', 'cis')
        cis_cfg.set('debug', 'cis', 'DEBUG')
        cfg_logging()

    def reset_log(self):  # pragma: debug
        r"""Resetting logging to prior value."""
        if self._old_loglevel is not None:
            cis_cfg.set('debug', 'cis', self._old_loglevel)
            cfg_logging()
            self._old_loglevel = None

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
            prefix = '%s(%s)' % (self.extra['cis_class'], self.name)
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
        return super(CisClass, self).error

    @property
    def exception(self):
        r"""Log an exception level message."""
        exc_info = sys.exc_info()
        if exc_info is not None and exc_info != (None, None, None):
            self.errors.append('ERROR')
            return super(CisClass, self).exception
        else:
            return self.error

    def raise_error(self, e):
        r"""Raise an exception, logging it first.

        Args:
            e (Exception): Exception to raise.

        Raises:
            The provided exception.

        """
        self.errors.append(repr(e))
        raise e

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
    def timeout_key(self):
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


class CisThread(threading.Thread, CisClass):
    r"""Thread for CiS that tracks when the thread is started and joined.

    Attributes:
        lock (threading.RLock): Lock for accessing the sockets from multiple
            threads.
        start_event (threading.Event): Event indicating that the thread was
            started.
        terminate_event (threading.Event): Event indicating that the thread
            should be terminated. The target must exit when this is set.

    """
    def __init__(self, name=None, target=None, args=(), kwargs=None,
                 daemon=False, group=None, **cis_kwargs):
        global _lock_registry
        if kwargs is None:
            kwargs = {}
        thread_kwargs = dict(name=name, target=target, group=group,
                             args=args, kwargs=kwargs)
        super(CisThread, self).__init__(**thread_kwargs)
        CisClass.__init__(self, self.name, **cis_kwargs)
        self._cis_target = target
        self._cis_args = args
        self._cis_kwargs = kwargs
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
        super(CisThread, self).start(*args, **kwargs)
        self._calling_thread = threading.current_thread()
        # print("Thread = %s, Called by %s" % (self.name, self._calling_thread.name))

    def run(self, *args, **kwargs):
        r"""Continue running until terminate event set."""
        self.debug("Starting method")
        try:
            super(CisThread, self).run(*args, **kwargs)
        except BaseException:  # pragma: debug
            self.exception("THREAD ERROR")
        finally:
            for k in ['_cis_target', '_cis_args', '_cis_kwargs']:
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


class CisThreadLoop(CisThread):
    r"""Thread that will run a loop until the terminate event is called."""
    def __init__(self, *args, **kwargs):
        super(CisThreadLoop, self).__init__(*args, **kwargs)
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
        while (self.is_alive() and (not self.was_loop) and
               (not T.is_out)):  # pragma: debug
            self.verbose_debug('Waiting for thread to enter loop...')
            self.sleep()
        self.stop_timeout(key_level=1, key=key)

    def before_loop(self):
        r"""Actions performed before the loop."""
        self.debug('')

    def run_loop(self, *args, **kwargs):
        r"""Actions performed on each loop iteration."""
        if self._cis_target:
            self._cis_target(*self._cis_args, **self._cis_kwargs)
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
                if ((self.main_terminated and
                     (not self._1st_main_terminated))):  # pragma: debug
                    self.on_main_terminated()
                else:
                    self.run_loop()
            self.set_break_flag()
        except BaseException:  # pragma: debug
            self.exception("THREAD ERROR")
            self.set_break_flag()
        finally:
            for k in ['_cis_target', '_cis_args', '_cis_kwargs']:
                if hasattr(self, k):
                    delattr(self, k)
        try:
            self.after_loop()
        except BaseException:  # pragma: debug
            self.exception("AFTER LOOP ERROR")

    def terminate(self, *args, **kwargs):
        r"""Also set break flag."""
        self.set_break_flag()
        super(CisThreadLoop, self).terminate(*args, **kwargs)
