from threading import Thread, Timer, RLock
from logging import info, debug, error, warn, exception, critical
import os
import time
import inspect
from cis_interface.config import cis_cfg
from cis_interface.tools import TimeOut


class Driver(Thread):
    r"""Base class for all drivers.

    Args:
        name (str): Driver name.
        yml (dict, optional): Dictionary of yaml specification options for this
            driver. Defaults to empty dict.
        env (dict, optional): Dictionary of environment variables that should
            be set when the driver starts. Defaults to {}.
        namespace (str, optional): Namespace for set of drivers running
            together. If not provided, the config option ('rmq', 'namespace')
            is used.
        rank (int, optional): Rank of the integration. Defaults to None.
        workingDir (str, optional): Working directory. If not provided, the
            current working directory is used.
        timeout (float, optional): Maximum time (in seconds) that should be
            spent waiting on a process. Defaults to 60.
        sleeptime (float, optional): Time that driver should sleep for when
            sleep is called. Defaults to 0.01.

    Attributes:
        name (str): Driver name.
        sleeptime (float): Time that driver should sleep for when sleep called.
        longsleep (float): Time that the driver will sleep for when waiting for
            longer tasks to complete (10x longer than sleeptime).
        timeout (float): Maximum time that should be spent waiting on a process.
        env (dict): Dictionary of environment variables.
        yml (dict): Dictionary of yaml specification options for this driver.
        namespace (str): Namespace for set of drivers running together.
        rank (int): Rank of the integration.
        workingDir (str): Working directory.
        errors (list): List of errors.

    """
    # =========================================================================
    # METHODS THAT MUST HAVE SUPER AT BEGINNING AND CAN BE OVERRIDEN BY CHILD
    # CLASSES TO ADD DRIVER FUNCTIONALITY. ALL OF THE CHILD CLASSES MUST HAVE
    # COMPATIBLE FORMATS (THE SAME NAMED ARGUMENTS).
    def __init__(self, name, yml={}, env={}, namespace=None, rank=None,
                 workingDir=None, timeout=60.0, sleeptime=0.01):
        # Check if thread initialized to avoid doing it twice for drivers
        # with multiple inheritance that both need to call __init__
        if getattr(self, '_thread_initialized', False):  # pragma: debug
            raise Exception("Thread already initialized. " +
                            "Check multiple inheritance")
        super(Driver, self).__init__()
        self._thread_initialized = True
        self.debug()
        self.name = name
        self.sleeptime = sleeptime
        # if cis_cfg.get('debug', 'psi') == 'DEBUG':
        #     self.sleeptime = 1.0
        self.longsleep = self.sleeptime * 10
        self.timeout = timeout
        self._timeouts = {}
        # Set defaults
        if namespace is None:
            namespace = cis_cfg.get('rmq', 'namespace')
            self.debug("Setting namespace to %s", namespace)
        if workingDir is None:
            if isinstance(yml, dict) and ('workingDir' in yml):
                workingDir = yml['workingDir']
            else:
                workingDir = os.getcwd()
        # Assign things
        self.yml = yml
        self.env = env
        self.namespace = namespace
        self.rank = rank
        self.workingDir = workingDir
        self._term_meth = "terminate"
        self._terminated = False
        self.lock = RLock()
        self.errors = []

    # def __del__(self):
    #     # self.debug('~')
    #     if self.isAlive():  # pragma: debug
    #         self.terminate()
    #         self.join()
    #     assert(not self.isAlive())
    #     self.cleanup()

    def run(self):
        r"""Run something in a seperate thread."""
        self.debug(':run()')

    @property
    def is_valid(self):
        r"""bool: True if the driver is functional."""
        return True

    def stop(self):
        r"""Stop the driver."""
        if self._terminated:
            self.debug(':stop() Driver already terminated.')
            return
        self.debug(':stop()')
        self._term_meth = 'stop'
        self.graceful_stop()
        self.terminate()

    def graceful_stop(self):
        r"""Gracefully stop the driver."""
        self.debug(':graceful_stop()')

    def terminate(self):
        r"""Stop the driver, without attempting to allow it to finish."""
        if self._terminated:
            self.debug(':terminated() Driver already terminated.')
            return
        self.debug(':terminate()')
        T = self.start_timeout()
        while self.is_alive() and (not T.is_out):
            self.sleep()
        self.stop_timeout()
        self.on_exit()
        self._terminated = True

    def on_exit(self):
        r"""Processes that should be run when the driver exits."""
        self.debug(':on_exit()')

    def on_model_exit(self):
        r"""Processes that should be run when an associated model exits."""
        self.debug(':on_model_exit()')

    def cleanup(self):
        r"""Processes that should be run to clean up a driver that is not
        running."""
        self.debug(':cleanup()')

    def wait(self, timeout=0.0):
        r"""Wait until model finish to return.

        Args:
            timeout (float, optional): Maximum time that should be waited for
                the driver to finish. Defaults to 0 and is infinite.

        """
        T = self.start_timeout(timeout)
        while self.is_alive() and not T.is_out:
            self.debug('Waiting for driver to finish...')
            self.sleep()
        self.stop_timeout()

    def printStatus(self):
        r"""Print the driver status."""
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

    # def copy_env(self, solf=None):
    #     r"""Copy environment variables over from another model or the overall
    #     environment.

    #     Args:
    #         solf (object, optional): Driver that environment variables should
    #             be copied from. Defaults to None and the current environment
    #             variables are copied over.

    #     """
    #     if solf is None:
    #         self.env.update(os.environ)
    #     else:
    #         self.env.update(solf.env)

    # =========================================================================
            
    @property
    def logger_prefix(self):
        r"""Prefix to add to logger messages."""
        stack = inspect.stack()
        the_class = os.path.splitext(os.path.basename(
            stack[2][0].f_globals["__file__"]))[0]
        return '%s(%s)' % (the_class, self.name)

    def sleep(self, t=None):
        r"""Have the driver sleep for some period of time.

        Args:
            t (float, optional): Time that driver should sleep for. If not
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
                driver and function/method (See `timeout_key`).

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
                Defaults to None and is set by the calling driver and
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
                Defaults to None and is set by the calling driver and
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
        r"""Log a message at level 1000 that is prepended with the driver class
        and name. These messages will always be printed.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        if not isinstance(fmt_str, str):
            fmt_str = str(fmt_str)
        print(self.logger_prefix + fmt_str % args)

    def info(self, fmt_str='', *args):
        r"""Log an info message that is prepended with the driver class and
        name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        if not isinstance(fmt_str, str):
            fmt_str = str(fmt_str)
        info(self.logger_prefix + fmt_str, *args)

    def debug(self, fmt_str='', *args):
        r"""Log a debug message that is prepended with the driver class and
        name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        if not isinstance(fmt_str, str):
            fmt_str = str(fmt_str)
        debug(self.logger_prefix + fmt_str, *args)

    def critical(self, fmt_str='', *args):
        r"""Log a critical message that is prepended with the driver class and
        name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        if not isinstance(fmt_str, str):
            fmt_str = str(fmt_str)
        critical(self.logger_prefix + fmt_str, *args)

    def warn(self, fmt_str='', *args):
        r"""Log a warning message that is prepended with the driver class and
        name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        if not isinstance(fmt_str, str):
            fmt_str = str(fmt_str)
        warn(self.logger_prefix + fmt_str, *args)

    def error(self, fmt_str='', *args):
        r"""Log an error message that is prepended with the driver class and
        name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        if not isinstance(fmt_str, str):
            fmt_str = str(fmt_str)
        error(self.logger_prefix + fmt_str, *args)
        self.errors.append((self.logger_prefix + fmt_str) % args)

    def exception(self, fmt_str='', *args):
        r"""Log an exception message that is prepended with the driver class
        ane name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        if not isinstance(fmt_str, str):
            fmt_str = str(fmt_str)
        exception(self.logger_prefix + fmt_str, *args)
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
