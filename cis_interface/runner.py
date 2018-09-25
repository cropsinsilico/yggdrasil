"""This module provides tools for running models using cis_interface."""
import sys
import logging
# import atexit
import os
import signal
from pprint import pformat
from itertools import chain
import socket
from cis_interface.tools import CisClass
from cis_interface.config import cis_cfg, cfg_environment
from cis_interface import platform, backwards, yamlfile
from cis_interface.drivers import create_driver, import_driver


COLOR_TRACE = '\033[30;43;22m'
COLOR_NORMAL = '\033[0m'


# def setup_cis_logging(prog, level=None):
#     r"""Set the log lovel based on environment variable 'CIS_DEBUG'. If the
#     variable is not set, the log level is set to 'NOTSET'.

#     Args:
#         prog (str): Name to prepend log messages with.
#         level (str, optional): String specifying the logging level. Defaults
#             to None and the environment variable 'CIS_DEBUG' is used.

#     """
#     if level is None:
#         level = cis_cfg.get('debug', 'cis', 'NOTSET')
#     logLevel = eval('logging.' + level)
#     logging.basicConfig(level=logLevel, stream=sys.stdout, format=COLOR_TRACE +
#                         prog + ': %(message)s' + COLOR_NORMAL)


class CisRunner(CisClass):
    r"""This class handles the orchestration of starting the model and
    IO drivers, monitoring their progress, and cleaning up on exit.

    Arguments:
        modelYmls (list): List of paths to yaml files specifying the models
            that should be run.
        namespace (str): Name that should be used to uniquely identify any RMQ
            exchange.
        host (str, optional): Name of the host that the models will be launched
            from. Defaults to None.
        rank (int, optional): Rank of this set of models if run in parallel.
            Defaults to 0.
        cis_debug_level (str, optional): Level for CiS debug messages. Defaults
            to environment variable 'CIS_DEBUG'.
        rmq_debug_level (str, optional): Level for RabbitMQ debug messages.
            Defaults to environment variable 'RMQ_DEBUG'.
        cis_debug_prefix (str, optional): Prefix for CiS debug messages.
            Defaults to namespace.

    Attributes:
        namespace (str): Name that should be used to uniquely identify any RMQ
            exchange.
        host (str): Name of the host that the models will be launched from.
        rank (int): Rank of this set of models if run in parallel.
        modeldrivers (dict): Model drivers associated with this run.
        inputdrivers (dict): Input drivers associated with this run.
        outputdrivers (dict): Output drivers associated with this run.
        serverdrivers (dict): The addresses associated with different server
            drivers.
        interrupt_time (float): Time of last interrupt signal.
        error_flag (bool): True if one or more models raises an error.

    ..todo:: namespace, host, and rank do not seem strictly necessary.

    """
    def __init__(self, modelYmls, namespace, host=None, rank=0,
                 cis_debug_level=None, rmq_debug_level=None,
                 cis_debug_prefix=None):
        super(CisRunner, self).__init__('runner')
        self.namespace = namespace
        self.host = host
        self.rank = rank
        self.modeldrivers = {}
        self.inputdrivers = {}
        self.outputdrivers = {}
        self.serverdrivers = {}
        self.interrupt_time = 0
        self._inputchannels = {}
        self._outputchannels = {}
        self._old_handlers = {}
        self.error_flag = False
        # Setup logging
        # if cis_debug_prefix is None:
        #     cis_debug_prefix = namespace
        # setup_cis_logging(cis_debug_prefix, level=cis_debug_level)
        # Update environment based on config
        cfg_environment()
        # Parse yamls
        drivers = yamlfile.parse_yaml(modelYmls)
        self.inputdrivers = drivers['input']
        self.outputdrivers = drivers['output']
        self.modeldrivers = drivers['model']
        for x in self.outputdrivers.values():
            self._outputchannels[x['args']] = x
        for x in self.inputdrivers.values():
            self._inputchannels[x['args']] = x
        # print(pformat(self.inputdrivers), pformat(self.outputdrivers),
        #       pformat(self.modeldrivers))
        # atexit.register(self.cleanup)

    def pprint(self, *args):
        r"""Print with color."""
        s = ''.join(str(i) for i in args)
        print((COLOR_TRACE + '{}' + COLOR_NORMAL).format(s))

    def signal_handler(self, sig, frame):
        r"""Terminate all drivers on interrrupt."""
        self.debug("Interrupt with signal %d", sig)
        now = backwards.clock_time()
        elapsed = now - self.interrupt_time
        self.debug('Elapsed time since last interrupt: %d s', elapsed)
        self.interrupt_time = now
        self.pprint(' ')
        self.pprint(80 * '*')
        if elapsed < 5:
            self.pprint('* %76s *' % 'Interrupted twice within 5 seconds: shutting down')
            self.pprint(80 * '*')
            # signal.siginterrupt(signal.SIGTERM, True)
            # signal.siginterrupt(signal.SIGINT, True)
            self.debug("Terminating models and closing all channels")
            self.terminate()
            self.pprint(80 * '*')
            # self.sleep(5)
            return 1
        else:
            self.pprint('* %76s *' % 'Interrupted: Displaying channel summary')
            self.pprint('* %76s *' % 'interrupt again (within 5 seconds) to exit')
            self.pprint(80 * '*')
            self.printStatus()
            self.pprint(80 * '*')
        self.debug('%d returns', sig)

    def _swap_handler(self, signum, signal_handler):
        self._old_handlers[signum] = signal.getsignal(signum)
        signal.signal(signum, signal_handler)
        if not platform._is_win:
            signal.siginterrupt(signum, False)
        
    def set_signal_handler(self, signal_handler=None):
        r"""Set the signal handler.

        Args:
            signal_handler (function, optional): Function that should handle
                received SIGINT and SIGTERM signals. Defaults to
                self.signal_handler.

        """
        if signal_handler is None:
            signal_handler = self.signal_handler
        self._swap_handler(signal.SIGINT, signal_handler)
        if not platform._is_win:
            self._swap_handler(signal.SIGTERM, signal_handler)
        else:  # pragma: windows
            self._swap_handler(signal.SIGBREAK, signal_handler)

    def reset_signal_handler(self):
        r"""Reset signal handlers to old ones."""
        for k, v in self._old_handlers.items():
            signal.signal(k, v)

    def run(self, signal_handler=None):
        r"""Run all of the models and wait for them to exit."""
        self.loadDrivers()
        self.startDrivers()
        self.set_signal_handler(signal_handler)
        self.waitModels()
        self.reset_signal_handler()
        self.closeChannels()
        self.cleanup()

    @property
    def all_drivers(self):
        r"""iterator: For all drivers."""
        return chain(self.inputdrivers.values(), self.outputdrivers.values(),
                     self.modeldrivers.values())

    def io_drivers(self, model=None):
        r"""Return the input and output drivers for one or all models.

        Args:
            model (str, optional): Name of a model that I/O drivers should be
                returned for. Defaults to None and all I/O drivers are returned.

        Returns:
            iterator: Access to list of I/O drivers.

        """
        if model is None:
            out = chain(self.inputdrivers.values(), self.outputdrivers.values())
        else:
            driver = self.modeldrivers[model]
            out = chain(driver.get('input_drivers', dict()),
                        driver.get('output_drivers', dict()))
        return out

    def createDriver(self, yml):
        r"""Create a driver instance from the yaml information.

        Args:
            yml (yaml): Yaml object containing driver information.

        Returns:
            object: An instance of the specified driver.

        """
        self.debug('Creating %s, a %s', yml['name'], yml['driver'])
        curpath = os.getcwd()
        if 'ClientDriver' in yml['driver']:
            yml.setdefault('comm_address', self.serverdrivers[yml['args']])
        if 'working_dir' in yml:
            os.chdir(yml['working_dir'])
        instance = create_driver(yml=yml, namespace=self.namespace,
                                 rank=self.rank, **yml)
        yml['instance'] = instance
        os.chdir(curpath)
        if 'ServerDriver' in yml['driver']:
            self.serverdrivers[yml['args']] = instance.comm_address
        return instance

    def createModelDriver(self, yml):
        r"""Create a model driver instance from the yaml information.

        Args:
            yml (yaml): Yaml object containing driver information.

        Returns:
            object: An instance of the specified driver.

        """
        yml['env'] = {}
        for iod in self.io_drivers(yml['name']):
            yml['env'].update(iod['instance'].env)
            iod['models'].append(yml['name'])
        drv = self.createDriver(yml)
        if 'client_of' in yml:
            for srv in yml['client_of']:
                self.modeldrivers[srv]['clients'].append(yml['name'])
        self.debug("Model %s:, env: %s",
                   yml['name'], pformat(yml['instance'].env))
        return drv

    def createInputDriver(self, yml):
        r"""Create an input driver instance from the yaml information.

        Args:
            yml (yaml): Yaml object containing driver information.

        Returns:
            object: An instance of the specified driver.

        """
        yml['models'] = []
        if yml['args'] not in self._outputchannels:
            if not os.path.isfile(yml['args']):
                raise Exception(("Input driver %s could not locate a " +
                                 "corresponding file or output channel %s") % (
                                     yml["name"], yml["args"]))
        drv = self.createDriver(yml)
        return drv

    def createOutputDriver(self, yml):
        r"""Create an output driver instance from the yaml information.

        Args:
            yml (yaml): Yaml object containing driver information.

        Returns:
            object: An instance of the specified driver.

        """
        from cis_interface.drivers import FileOutputDriver
        yml['models'] = []
        if yml['args'] in self._inputchannels:
            yml.setdefault('comm_env', {})
            yml['comm_env'] = self._inputchannels[yml['args']]['instance'].comm_env
            # yml['kwargs'].setdefault('comm_env', {})
            # yml['kwargs']['comm_env'] = self._inputchannels[
            #     yml['args']]['instance'].comm_env
        drv_cls = import_driver(yml['driver'])
        if yml['args'] not in self._inputchannels:
            try:
                assert(issubclass(drv_cls,
                                  FileOutputDriver.FileOutputDriver))
            except AssertionError:
                raise Exception(("Output driver %s is not a subclass of " +
                                 "FileOutputDriver and there is not a " +
                                 "corresponding input channel %s.") % (
                                     yml["name"], yml["args"]))
        else:
            
            # TODO: Add input comm environment variables somehow
            pass
        drv = self.createDriver(yml)
        return drv
        
    def loadDrivers(self):
        r"""Load all of the necessary drivers, doing the IO drivers first
        and adding IO driver environmental variables back tot he models."""
        self.debug('')
        driver = dict(name='name')
        try:
            # Create input drivers
            self.debug("Loading input drivers")
            for driver in self.inputdrivers.values():
                self.createInputDriver(driver)
            # Create output drivers
            self.debug("Loading output drivers")
            for driver in self.outputdrivers.values():
                self.createOutputDriver(driver)
            # Create model drivers
            self.debug("Loading model drivers")
            for driver in self.modeldrivers.values():
                self.createModelDriver(driver)
        except BaseException:  # pragma: debug
            self.error("%s could not be created.", driver['name'])
            self.terminate()
            raise

    def startDrivers(self):
        r"""Start drivers, starting with the IO drivers."""
        self.info('Starting I/O drivers and models on system ' +
                  '{} in namespace {} with rank {}'.format(
                      self.host, self.namespace, self.rank))
        driver = dict(name='name')
        try:
            # Start connections
            for driver in self.io_drivers():
                self.debug("Starting driver %s", driver['name'])
                d = driver['instance']
                if not d.was_started:
                    d.start()
            # Ensure connections in loop
            for driver in self.io_drivers():
                self.debug("Checking driver %s", driver['name'])
                d = driver['instance']
                d.wait_for_loop()
                assert(d.was_loop)
                assert(not d.errors)
            # Start models
            # self.sleep(1)  # on windows comms can take a while start
            for driver in self.modeldrivers.values():
                self.debug("Starting driver %s", driver['name'])
                d = driver['instance']
                for n2 in driver.get('client_of', []):
                    d2 = self.modeldrivers[n2]['instance']
                    if not d2.was_started:
                        self.debug("Starting server '%s' before client", d2.name)
                        d2.start()
                if not d.was_started:
                    d.start()
        except BaseException:  # pragma: debug
            self.error("%s did not start", driver['name'])
            self.terminate()
            raise
        self.debug('ALL DRIVERS STARTED')

    def waitModels(self):
        r"""Wait for all model drivers to finish. When a model finishes,
        join the thread and perform exits for associated IO drivers."""
        self.debug('')
        running = [d for d in self.modeldrivers.values()]
        dead = []
        while (len(running) > 0) and (not self.error_flag):
            for drv in running:
                d = drv['instance']
                if d.errors:  # pragma: debug
                    self.error('Error in model %s', drv['name'])
                    self.error_flag = True
                    break
                d.join(1)
                if not d.is_alive():
                    if not d.errors:
                        self.info("%s finished running.", drv['name'])
                        self.do_model_exits(drv)
                        self.debug("%s completed model exits.", drv['name'])
                        self.do_client_exits(drv)
                        self.debug("%s completed client exits.", drv['name'])
                        running.remove(drv)
                        self.info("%s finished exiting.", drv['name'])
                else:
                    self.info('%s still running', drv['name'])
            dead = []
            for drv in self.all_drivers:
                d = drv['instance']
                d.join(0.1)
                if not d.is_alive():
                    dead.append(drv['name'])
        for d in self.modeldrivers.values():
            if d['instance'].errors:
                self.error_flag = True
        if not self.error_flag:
            self.info('All models completed')
        else:
            self.error('One or more models generated errors.')
            self.terminate()
        self.debug('Returning')

    def do_model_exits(self, model):
        r"""Perform exits for IO drivers associated with a model.

        Args:
            model (dict): Dictionary of model parameters including any
                associated IO drivers.

        """
        for drv in self.io_drivers(model['name']):
            drv['models'].remove(model['name'])
            if not drv['instance'].is_alive():
                continue
            if (len(drv['models']) == 0):
                self.debug('on_model_exit %s', drv['name'])
                drv['instance'].on_model_exit()
    
    def do_client_exits(self, model):
        r"""Perform exits for IO drivers associated with a client model.

        Args:
            model (dict): Dictionary of model parameters including any
                associated IO drivers.

        """
        for srv_name in model.get('client_of', []):
            # Remove this client from list for server
            srv = self.modeldrivers[srv_name]
            srv['clients'].remove(model['name'])
            # Stop server if there are not any more clients
            if len(srv['clients']) == 0:
                iod = self.inputdrivers[srv_name]
                iod['instance'].on_client_exit()
                srv['instance'].stop()

    def terminate(self):
        r"""Immediately stop all drivers, beginning with IO drivers."""
        self.debug('')
        # self.closeChannels(force_stop=True)
        # self.debug('Stop models')
        for driver in self.all_drivers:
            if 'instance' in driver:
                self.debug('Stop %s', driver['name'])
                driver['instance'].terminate()
                # Terminate should ensure instance not alive
                assert(not driver['instance'].is_alive())
                # if driver['instance'].is_alive():
                #     driver['instance'].join()
        self.debug('Returning')

    def cleanup(self):
        r"""Perform cleanup operations for all drivers."""
        self.debug('')
        for driver in self.all_drivers:
            if 'instance' in driver:
                driver['instance'].cleanup()

    def printStatus(self):
        r"""Print the status of all drivers, starting with the IO drivers."""
        self.debug('')
        for driver in self.all_drivers:
            if 'instance' in driver:
                driver['instance'].printStatus()

    def closeChannels(self, force_stop=False):
        r"""Stop IO drivers and join the threads.

        Args:
            force_stop (bool, optional): If True, the terminate method is
                used to stop the drivers. Otherwise, the stop method is used.
                The stop method will try to exit gracefully while terminate
                will exit as quickly as possible. Defaults to False.

        """
        self.debug('')
        drivers = [i for i in self.io_drivers()]
        for drv in drivers:
            if 'instance' in drv:
                driver = drv['instance']
                if driver.is_alive():  # pragma: debug
                    self.debug("Stopping %s", drv['name'])
                    if force_stop or self.error_flag:
                        driver.terminate()
                    else:
                        driver.stop()
                    self.debug("Stop(%s) returns", drv['name'])
        self.debug('Channel Stops DONE')
        for drv in drivers:
            if 'instance' in drv:
                driver = drv['instance']
                assert(not driver.is_alive())
                # self.debug("Join %s", drv['name'])
                # if driver.is_alive():
                #     driver.join()
                # self.debug("Join %s done", drv['name'])
        self.debug('Returning')

        
def get_runner(models, **kwargs):
    r"""Get runner for a set of models, getting run information from the
    environment.

    Args:
        models (list): List of yaml files containing information on the models
            that should be run.
        **kwargs: Additonal keyword arguments are passed to CisRunner.

    Returns:
        CisRunner: Runner for the provided models.

    Raises:
        Exception: If config option 'namespace' in 'rmq' section not set.

    """
    # Get environment variables
    logger = logging.getLogger(__name__)
    namespace = kwargs.pop('namespace', cis_cfg.get('rmq', 'namespace', False))
    if not namespace:  # pragma: debug
        raise Exception('rmq:namespace not set in config file')
    rank = os.environ.get('PARALLEL_SEQ', '0')
    host = socket.gethostname()
    os.environ['CIS_RANK'] = rank
    os.environ['CIS_HOST'] = host
    rank = int(rank)
    kwargs.update(rank=rank, host=host)
    # Run
    logger.debug("Running in %s with path %s namespace %s rank %d",
                 os.getcwd(), sys.path, namespace, rank)
    cisRunner = CisRunner(models, namespace, **kwargs)
    return cisRunner
