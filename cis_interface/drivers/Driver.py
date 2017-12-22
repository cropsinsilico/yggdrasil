from threading import Thread, RLock
import os
from cis_interface.config import cis_cfg
from cis_interface.tools import CisClass


class Driver(CisClass, Thread):
    r"""Base class for all drivers.

    Args:
        name (str): Driver name.
        yml (dict, optional): Dictionary of yaml specification options for this
            driver. Defaults to empty dict.
        env (dict, optional): Dictionary of environment variables that should
            be set when the driver starts. Defaults to {}.
        comm_env (dict, optional): Dictionary of environment variables for
            paired IO communication drivers. Defaults to {}.
        namespace (str, optional): Namespace for set of drivers running
            together. If not provided, the config option ('rmq', 'namespace')
            is used.
        rank (int, optional): Rank of the integration. Defaults to None.

    Attributes:
        name (str): Driver name.
        env (dict): Dictionary of environment variables.
        comm_env (dict): Dictionary of environment variables for paired IO
            communication drivers.
        yml (dict): Dictionary of yaml specification options for this driver.
        namespace (str): Namespace for set of drivers running together.
        rank (int): Rank of the integration.

    """
    # =========================================================================
    # METHODS THAT MUST HAVE SUPER AT BEGINNING AND CAN BE OVERRIDEN BY CHILD
    # CLASSES TO ADD DRIVER FUNCTIONALITY. ALL OF THE CHILD CLASSES MUST HAVE
    # COMPATIBLE FORMATS (THE SAME NAMED ARGUMENTS).
    def __init__(self, name, yml=None, env=None, comm_env=None, namespace=None,
                 rank=None, **kwargs):
        if yml is None:
            yml = {}
        if env is None:
            env = {}
        if comm_env is None:
            comm_env = {}
        # Check if thread initialized to avoid doing it twice for drivers
        # with multiple inheritance that both need to call __init__
        if getattr(self, '_thread_initialized', False):  # pragma: debug
            raise Exception("Thread already initialized. " +
                            "Check multiple inheritance")
        Thread.__init__(self)
        super(Driver, self).__init__(name, **kwargs)
        self._thread_initialized = True
        self.debug()
        self.name = name
        # if cis_cfg.get('debug', 'psi') == 'DEBUG':
        #     self.sleeptime = 1.0
        # Set defaults
        if namespace is None:
            namespace = cis_cfg.get('rmq', 'namespace')
            self.debug("Setting namespace to %s", namespace)
        if kwargs.get('workingDir', None) is None:
            if isinstance(yml, dict) and ('workingDir' in yml):
                self.workingDir = yml['workingDir']
            else:
                self.workingDir = os.getcwd()
        # Assign things
        self.yml = yml
        self.env = env
        self.comm_env = comm_env
        self.namespace = namespace
        self.rank = rank
        self._term_meth = "terminate"
        self._terminated = False
        self.lock = RLock()

    # def __del__(self):
    #     # self.debug('~')
    #     if self.isAlive():  # pragma: debug
    #         self.terminate()
    #         self.join()
    #     assert(not self.isAlive())
    #     self.cleanup()

    def run(self):
        r"""Run something in a seperate thread."""
        self.debug()

    @property
    def is_valid(self):
        r"""bool: True if the driver is functional."""
        return True

    def stop(self):
        r"""Stop the driver."""
        if self._terminated:
            self.debug('Driver already terminated.')
            return
        self.debug()
        self._term_meth = 'stop'
        self.graceful_stop()
        self.terminate()

    def graceful_stop(self):
        r"""Gracefully stop the driver."""
        self.debug()

    def terminate(self):
        r"""Stop the driver, without attempting to allow it to finish."""
        if self._terminated:
            self.debug('Driver already terminated.')
            return
        self.debug()
        T = self.start_timeout()
        while self.is_alive() and (not T.is_out):
            self.sleep()
        self.stop_timeout()
        self.on_exit()
        self._terminated = True
        self.debug('Returning')

    def on_exit(self):
        r"""Processes that should be run when the driver exits."""
        self.debug()

    def on_model_exit(self):
        r"""Processes that should be run when an associated model exits."""
        self.debug()

    def cleanup(self):
        r"""Processes that should be run to clean up a driver that is not
        running."""
        self.debug()

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
