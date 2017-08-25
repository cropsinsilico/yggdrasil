from threading import Thread
from logging import info, debug, error, warn, exception, critical
import os
import sys
import time
import inspect
PY_MAJOR_VERSION = sys.version_info[0]


class Driver(Thread):
    r"""Base class for all drivers.

    Args:
        name (str): Driver name.
        yml (dict, optional): Dictionary of yaml specification options for this
            driver. Defaults to empty dict.
        namespace (str, optional): Namespace for set of drivers running 
            together. If not provided, the environment variable 'PSI_NAMESPACE'
            is used.
        rank (int, optional): Rank of the integration. Defaults to None.
        workingDir (str, optional): Working directory. If not provided, the 
            current working directory is used.

    Attributes:
        name (str): Driver name.
        sleeptime (float): Time that driver should sleep for when sleep called.
        longsleep (float): Time that the driver will sleep for when waiting for
            longer tasks to complete (10x longer than sleeptime). 
        yml (dict): Dictionary of yaml specification options for this driver.
        namespace (str): Namespace for set of drivers running together.
        rank (int): Rank of the integration.
        workingDir (str): Working directory.

    """
    # =========================================================================
    # METHODS THAT MUST HAVE SUPER AT BEGINNING AND CAN BE OVERRIDEN BY CHILD
    # CLASSES TO ADD DRIVER FUNCTIONALITY. ALL OF THE CHILD CLASSES MUST HAVE
    # COMPATIBLE FORMATS (THE SAME NAMED ARGUMENTS).
    def __init__(self, name, yml={}, namespace=None, rank=None,
                 workingDir=None):
        # Check if thread initialized to avoid doing it twice for drivers
        # with multiple inheritance that both need to call __init__
        if getattr(self, '_thread_initialized', False):
            raise Exception("Thread already initialized. Check multiple inheritance")
        super(Driver, self).__init__()
        self._thread_initialized = True
        self.debug()
        self.name = name
        self.sleeptime = 0.25
        if os.environ['PSI_DEBUG'] == 'DEBUG':
            self.sleeptime = 1.0
        self.longsleep = self.sleeptime*10
        # Set defaults
        if namespace is None:
            print("Setting namespace to %s" % os.environ['PSI_NAMESPACE'])
            namespace = os.environ['PSI_NAMESPACE']
        if workingDir is None:
            if isinstance(yml, dict) and ('workingDir' in yml):
                workingDir = yml['workingDir']
            else:
                workingDir = os.getcwd()
        # Assign things
        self.yml = yml
        self.namespace = namespace
        self.rank = rank
        self.workingDir = workingDir
        self._term_meth = None

    def __del__(self):
        self.debug('~')
        if self.isAlive():
            self.terminate()

    def run(self):
        r"""Run something in a seperate thread."""
        self.debug(':run()')

    def stop(self):
        r"""Stop the driver."""
        self.debug(':stop()')
        self._term_meth = 'stop'
        self.terminate()

    def terminate(self):
        r"""Stop the driver, without attempting to allow it to finish."""
        self.debug(':terminate()')
        if self._term_meth is None:
            self._term_meth = 'terminate'

    def printStatus(self):
        r"""Print the driver status."""
        error('%s(%s): state:', self.__module__, self.name)

    # =========================================================================
            
    @property
    def logger_prefix(self):
        r"""Prefix to add to logger messages."""
        stack = inspect.stack()
        the_class = os.path.splitext(os.path.basename(stack[2][0].f_globals["__file__"]))[0]
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

    def info(self, fmt_str='', *args):
        r"""Print a info message that is prepended with the driver class and
        name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        if not isinstance(fmt_str, str):
            fmt_str = str(fmt_str)
        info(self.logger_prefix + fmt_str, *args)

    def debug(self, fmt_str='', *args):
        r"""Print a debug message that is prepended with the driver class and
        name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        if not isinstance(fmt_str, str):
            fmt_str = str(fmt_str)
        debug(self.logger_prefix + fmt_str, *args)

    def critical(self, fmt_str='', *args):
        r"""Print a critical message that is prepended with the driver class and
        name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        if not isinstance(fmt_str, str):
            fmt_str = str(fmt_str)
        critical(self.logger_prefix + fmt_str, *args)

    def warn(self, fmt_str='', *args):
        r"""Print a warning message that is prepended with the driver class and
        name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        if not isinstance(fmt_str, str):
            fmt_str = str(fmt_str)
        warn(self.logger_prefix + fmt_str, *args)

    def error(self, fmt_str='', *args):
        r"""Print a error message that is prepended with the driver class and
        name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        if not isinstance(fmt_str, str):
            fmt_str = str(fmt_str)
        error(self.logger_prefix + fmt_str, *args)

    def exception(self, fmt_str='', *args):
        r"""Print a exception message that is prepended with the driver class
        ane name.

        Args:
            fmt_str (str, optional): Format string.
            \*args: Additional arguments are formated using the format string.

        """
        if not isinstance(fmt_str, str):
            fmt_str = str(fmt_str)
        exception(self.logger_prefix + fmt_str, *args)

    def wait(self):
        r"""Wait until model finish to return."""
        while self.isAlive():
            self.debug('Waiting for model to finish...')
            self.sleep()

