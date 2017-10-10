"""This modules offers various tools."""
from threading import Timer
from logging import info, debug, error, warn, exception, critical
import os
import sys
import inspect
import time
from cis_interface import backwards


# OS X limit is 2kb
PSI_MSG_MAX = 1024 * 2
PSI_MSG_EOF = backwards.unicode2bytes("EOF!!!")


def eval_kwarg(x):
    r"""If x is a string, eval it. Otherwise just return it.

    Args:
        x (str, obj): String to be evaluated as an object or an object.

    Returns:
        obj: Evaluation result of x for strings if x is a string. x otherwise.

    """
    if isinstance(x, str):
        try:
            return eval(x)
        except NameError:
            return x
    return x


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
        self.start_time = time.clock()

    @property
    def elapsed(self):
        r"""float: Total time that has elapsed since the start."""
        return time.clock() - self.start_time
    
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

    def printStatus(self):
        r"""Print the class status."""
        error('%s(%s): state:', self.__module__, self.name)

    def sched_task(self, t, func, args=[], kwargs={}):
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

        """
        tobj = Timer(t, func, args=args, kwargs=kwargs)
        tobj.start()

    @property
    def logger_prefix(self):
        r"""Prefix to add to logger messages."""
        stack = inspect.stack()
        the_class = os.path.splitext(os.path.basename(
            stack[2][0].f_globals["__file__"]))[0]
        return '%s(%s)' % (the_class, self.name)

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
        if t.is_out:
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
        if not isinstance(fmt_str, str):
            fmt_str = str(fmt_str)
        print(self.logger_prefix + fmt_str % args)

    def info(self, fmt_str='', *args):
        r"""Log an info message that is prepended with the class and name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        if not isinstance(fmt_str, str):
            fmt_str = str(fmt_str)
        info(self.logger_prefix + fmt_str, *args)

    def debug(self, fmt_str='', *args):
        r"""Log a debug message that is prepended with the class and name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        if not isinstance(fmt_str, str):
            fmt_str = str(fmt_str)
        debug(self.logger_prefix + fmt_str, *args)

    def critical(self, fmt_str='', *args):
        r"""Log a critical message that is prepended with the class and name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        if not isinstance(fmt_str, str):
            fmt_str = str(fmt_str)
        critical(self.logger_prefix + fmt_str, *args)

    def warn(self, fmt_str='', *args):
        r"""Log a warning message that is prepended with the class and name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        if not isinstance(fmt_str, str):
            fmt_str = str(fmt_str)
        warn(self.logger_prefix + fmt_str, *args)

    def error(self, fmt_str='', *args):
        r"""Log an error message that is prepended with the class and name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        if not isinstance(fmt_str, str):
            fmt_str = str(fmt_str)
        error(self.logger_prefix + fmt_str, *args)
        self.errors.append((self.logger_prefix + fmt_str) % args)

    def exception(self, fmt_str='', *args):
        r"""Log an exception message that is prepended with the class name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        if not isinstance(fmt_str, str):
            fmt_str = str(fmt_str)
        exc_info = sys.exc_info()
        if exc_info is not None and exc_info != (None, None, None):
            exception(self.logger_prefix + fmt_str, *args)
        else:
            error(self.logger_prefix + fmt_str, *args)
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
