import os
from cis_interface.config import cis_cfg
from cis_interface import tools


class Driver(tools.CisThreadLoop):
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
        super(Driver, self).__init__(name, **kwargs)
        self._thread_initialized = True
        self.debug('')
        # if cis_cfg.get('debug', 'cis') == 'DEBUG':
        #     self.sleeptime = 1.0
        # Set defaults
        if namespace is None:
            namespace = cis_cfg.get('rmq', 'namespace')
            self.debug("Setting namespace to %s", namespace)
        if kwargs.get('working_dir', None) is None:
            if isinstance(yml, dict) and ('working_dir' in yml):
                self.working_dir = yml['working_dir']
            else:
                self.working_dir = os.getcwd()
        # Assign things
        self.yml = yml
        self.env = env
        self.comm_env = comm_env
        self.namespace = namespace
        self.rank = rank
        self._term_meth = "terminate"

    @property
    def is_valid(self):
        r"""bool: True if the driver is functional."""
        return True

    def stop(self):
        r"""Stop the driver."""
        if self.was_terminated:
            self.debug('Driver already terminated.')
            return
        self.debug('')
        self._term_meth = 'stop'
        self.graceful_stop()
        self.terminate()

    def graceful_stop(self):
        r"""Gracefully stop the driver."""
        self.debug('')

    def do_terminate(self):
        r"""Actions that should stop the driver."""
        self.debug('Returning')

    def terminate(self):
        r"""Stop the driver, without attempting to allow it to finish."""
        if self.was_terminated:
            self.debug('Driver already terminated.')
            return
        self.do_terminate()
        self.debug('')
        super(Driver, self).terminate()
        self.debug('Returning')

    def on_model_exit(self):
        r"""Processes that should be run when an associated model exits."""
        self.debug('')
