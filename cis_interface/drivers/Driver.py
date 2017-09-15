from threading import Thread, Timer, Lock
from logging import info, debug, error, warn, exception, critical
import os
import time
import inspect
from cis_interface.config import cis_cfg


class Driver(Thread):
    r"""Base class for all drivers.

    Args:
        name (str): Driver name.
        yml (dict, optional): Dictionary of yaml specification options for this
            driver. Defaults to empty dict.
        env (dict, optional): Dictionary of environment variables that should
            be set when the driver starts. Defaults to {}.
        namespace (str, optional): Namespace for set of drivers running
            together. If not provided, the environment variable 'PSI_NAMESPACE'
            is used.
        rank (int, optional): Rank of the integration. Defaults to None.
        workingDir (str, optional): Working directory. If not provided, the
            current working directory is used.
        timeout (float, optional): Maximum time (in seconds) that should be
            spent waiting on a process. Defaults to 60.

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

    """
    # =========================================================================
    # METHODS THAT MUST HAVE SUPER AT BEGINNING AND CAN BE OVERRIDEN BY CHILD
    # CLASSES TO ADD DRIVER FUNCTIONALITY. ALL OF THE CHILD CLASSES MUST HAVE
    # COMPATIBLE FORMATS (THE SAME NAMED ARGUMENTS).
    def __init__(self, name, yml={}, env={}, namespace=None, rank=None,
                 workingDir=None, timeout=60.0):
        # Check if thread initialized to avoid doing it twice for drivers
        # with multiple inheritance that both need to call __init__
        if getattr(self, '_thread_initialized', False):  # pragma: debug
            raise Exception("Thread already initialized. " +
                            "Check multiple inheritance")
        super(Driver, self).__init__()
        self._thread_initialized = True
        self.debug()
        self.name = name
        self.sleeptime = 0.001  # 25
        # if cis_cfg.get('debug', 'psi') == 'DEBUG':
        #     self.sleeptime = 1.0
        self.longsleep = self.sleeptime * 10
        self.timeout = timeout
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
        self.lock = Lock()

    def __del__(self):
        # self.debug('~')
        if self.isAlive():  # pragma: debug
            self.terminate()
        self.cleanup()

    def run(self):
        r"""Run something in a seperate thread."""
        self.debug(':run()')

    def stop(self):
        r"""Stop the driver."""
        self.debug(':stop()')
        self._term_meth = 'stop'
        self.graceful_stop()
        self.terminate()

    def graceful_stop(self):
        r"""Gracefully stop the driver."""
        self.debug(':graceful_stop()')

    def terminate(self):
        r"""Stop the driver, without attempting to allow it to finish."""
        self.debug(':terminate()')
        self.on_exit()

    def on_exit(self):
        r"""Processes that should be run when the driver exits."""
        self.debug(':on_exit()')

    def cleanup(self):
        r"""Processes that should be run to clean up a driver that is not
        running."""
        self.debug(':cleanup()')

    def wait(self):
        r"""Wait until model finish to return."""
        while self.isAlive():
            self.debug('Waiting for model to finish...')
            self.sleep()

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
