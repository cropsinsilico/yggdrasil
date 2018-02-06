"""This module provides tools for running models using cis_interface."""
import sys
import logging
import os
import time
import signal
from pprint import pformat
from itertools import chain
import socket
from cis_interface.tools import CisClass, parse_yaml
from cis_interface.config import cis_cfg, cfg_environment
from cis_interface import drivers, platform
from cis_interface.drivers import create_driver


COLOR_TRACE = '\033[30;43;22m'
COLOR_NORMAL = '\033[0m'


# def setup_cis_logging(prog, level=None):
#     r"""Set the log lovel based on environment variable 'PSI_DEBUG'. If the
#     variable is not set, the log level is set to 'NOTSET'.

#     Args:
#         prog (str): Name to prepend log messages with.
#         level (str, optional): String specifying the logging level. Defaults
#             to None and the environment variable 'PSI_DEBUG' is used.

#     """
#     if level is None:
#         level = cis_cfg.get('debug', 'psi', 'NOTSET')
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
            to environment variable 'PSI_DEBUG'.
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
        self.error_flag = False
        # Setup logging
        # if cis_debug_prefix is None:
        #     cis_debug_prefix = namespace
        # setup_cis_logging(cis_debug_prefix, level=cis_debug_level)
        # Update environment based on config
        cfg_environment()
        # Parse yamls
        if isinstance(modelYmls, str):
            modelYmls = [modelYmls]
        for modelYml in modelYmls:
            self.parseModelYaml(modelYml)
        # print(pformat(self.inputdrivers), pformat(self.outputdrivers),
        #       pformat(self.modeldrivers))

    def parseModelYaml(self, modelYml):
        r"""Parse supplied yaml, adding yamldir and doing mustache replace.

        Args:
            modelYml (str): Path to yaml file containing model info.

        Raises:
            IOError: If the yaml file cannot be located.

        """
        yamlpath = os.path.realpath(modelYml)
        yamldir = os.path.dirname(yamlpath)
        if not os.path.isfile(yamlpath):
            raise IOError("Unable locate yaml file %s" % yamlpath)
        # Open file and parse yaml
        self.info("Loading yaml %s", yamlpath)
        yamlparsed = parse_yaml(yamlpath)
        self.debug("After stache: %s", pformat(yamlparsed))
        # Store parsed models
        yml_models = yamlparsed.get('models', [])
        if 'model' in yamlparsed:
            yml_models.append(yamlparsed['model'])
        for yml in yml_models:
            self.add_driver('model', yml, yamldir)

    def add_driver(self, dtype, yaml, yamldir):
        r"""Add a driver to the appropriate driver dictionary with yamldir.

        Args:
            dtype (str): Driver type. Should be 'input', 'output',or 'model'.
            yaml (dict): YAML dictionary for the driver.
            yamldir (str): Full path to directory where the yaml is stored.

        Raises:
            ValueError: If dtype is not 'input', 'output',or 'model'.
            ValueError: If the driver name already exists.

        """
        if dtype == 'input':
            dd = self.inputdrivers
            self._inputchannels[yaml['args']] = yaml
        elif dtype == 'output':
            dd = self.outputdrivers
            self._outputchannels[yaml['args']] = yaml
        elif dtype == 'model':
            yaml.setdefault('inputs', [])
            yaml.setdefault('outputs', [])
            # Add server driver
            if yaml.get('is_server', False):
                srv = {'name': yaml['name'],
                       'driver': 'ServerDriver',
                       'args': yaml['name'] + '_SERVER'}
                yaml['inputs'].append(srv)
                yaml['clients'] = []
            # Add client driver
            if yaml.get('client_of', []):
                srv_names = yaml['client_of']
                if isinstance(srv_names, str):
                    srv_names = [srv_names]
                yaml['client_of'] = srv_names
                for srv in srv_names:
                    cli = {'name': '%s_%s' % (srv, yaml['name']),
                           'driver': 'ClientDriver',
                           'args': srv + '_SERVER'}
                    yaml['outputs'].append(cli)
            # Add I/O drivers for this model
            for inp in yaml['inputs']:
                inp['model_driver'] = yaml['name']
                self.add_driver('input', inp, yamldir)
            for inp in yaml['outputs']:
                inp['model_driver'] = yaml['name']
                self.add_driver('output', inp, yamldir)
            dd = self.modeldrivers
        else:
            raise ValueError("%s is not a recognized driver type." % dtype)
        # Check to make sure there arn't two drivers with the same name
        if yaml['name'] in dd:
            raise ValueError("%s is already a registered %s driver." % (
                yaml['name'], dtype))
        # Copy keywords
        if 'kwargs' in yaml:
            raise RuntimeError(("The yaml specs for driver %s includes the " +
                                "keyword 'kwargs' which is reserved. " +
                                "Please remove it.") % yaml['name'])
        yaml['kwargs'] = {}
        kws_ignore = ['name', 'driver', 'args', 'kwargs', 'onexit',
                      'input', 'inputs', 'output', 'outputs', 'clients',
                      'model_driver']
        for k in yaml:
            if k not in kws_ignore:
                yaml['kwargs'][k] = yaml[k]
        yaml['workingDir'] = yamldir
        dd[yaml['name']] = yaml

    def pprint(self, *args):
        r"""Print with color."""
        s = ''.join(str(i) for i in args)
        print((COLOR_TRACE + '{}' + COLOR_NORMAL).format(s))

    def signal_handler(self, sig, frame):
        r"""Terminate all drivers on interrrupt."""
        self.debug("Interrupt with signal %d", sig)
        now = time.time()
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
        
    def set_signal_handler(self, signal_handler=None):
        r"""Set the signal handler.

        Args:
            signal_handler (function, optional): Function that should handle
                received SIGINT and SIGTERM signals. Defaults to
                self.signal_handler.

        """
        if signal_handler is None:
            signal_handler = self.signal_handler
        signal.signal(signal.SIGINT, signal_handler)
        if not platform._is_win:
            signal.signal(signal.SIGTERM, signal_handler)
            signal.siginterrupt(signal.SIGTERM, False)
            signal.siginterrupt(signal.SIGINT, False)
        else:
            signal.signal(signal.SIGBREAK, signal_handler)
            if False:
                import ctypes
                handler = ctypes.WINFUNCTYPE(ctypes.c_int,
                                             ctypes.c_uint)(signal_handler)
                ctypes.windll.kernel32.SetConsoleCtrlHandler(handler, True)

    def run(self, signal_handler=None):
        r"""Run all of the models and wait for them to exit."""
        self.loadDrivers()
        self.startDrivers()
        self.set_signal_handler(signal_handler)
        self.waitModels()
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
            out = chain(driver.get('inputs', dict()),
                        driver.get('outputs', dict()))
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
            yml['kwargs'].setdefault('comm_address',
                                     self.serverdrivers[yml['args']])
        os.chdir(yml['workingDir'])
        instance = create_driver(yml['driver'], yml['name'], yml['args'],
                                 yml=yml, env=yml.get('env', {}),
                                 namespace=self.namespace, rank=self.rank,
                                 workingDir=yml['workingDir'],
                                 **yml['kwargs'])
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
        if yml['args'] not in self._outputchannels:
            try:
                norm_path = os.path.normpath(os.path.join(
                    yml['workingDir'], yml['args']))
                assert(os.path.isfile(norm_path))
            except AssertionError:
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
        if yml['args'] in self._inputchannels:
            yml['kwargs'].setdefault('comm_env', {})
            yml['kwargs']['comm_env'] = self._inputchannels[
                yml['args']]['instance'].comm_env
        drv = self.createDriver(yml)
        if yml['args'] not in self._inputchannels:
            try:
                assert(issubclass(drv.__class__,
                                  drivers.FileOutputDriver.FileOutputDriver))
            except AssertionError:
                raise Exception(("Output driver %s is not a subclass of " +
                                 "FileOutputDriver and there is not a " +
                                 "corresponding input channel %s.") % (
                                     yml["name"], yml["args"]))
        else:
            
            # TODO: Add input comm environment variables somehow
            pass
        return drv
        
    def loadDrivers(self):
        r"""Load all of the necessary drivers, doing the IO drivers first
        and adding IO driver environmental variables back tot he models."""
        self.debug()
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
            for driver in self.all_drivers:
                self.debug("Starting driver %s", driver['name'])
                d = driver['instance']
                d.start()
        except BaseException:  # pragma: debug
            self.error("%s did not start", driver['name'])
            self.terminate()
            raise
        self.debug('ALL DRIVERS STARTED')

    def waitModels(self):
        r"""Wait for all model drivers to finish. When a model finishes,
        join the thread and perform exits for associated IO drivers."""
        self.debug()
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
                    self.do_model_exits(drv)
                    running.remove(drv)
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
        r"""Perform exists for IO drivers associated with a model.

        Args:
            model (dict): Dictionary of model parameters including any
                associated IO drivers.

        """
        # Stop associated server if not more clients
        for srv_name in model.get('client_of', []):
            # Stop client IO driver
            iod = self.outputdrivers["%s_%s" % (srv_name, model['name'])]
            iod['instance'].on_model_exit()
            # Remove this client from list for server
            srv = self.modeldrivers[srv_name]
            srv['clients'].remove(model['name'])
            # Stop server if there are not any more clients
            if len(srv['clients']) == 0:
                iod = self.inputdrivers[srv_name]
                iod['instance'].on_model_exit()
                srv['instance'].stop()
                # self.do_model_exits(srv)
        # Stop associated IO drivers
        for drv in self.io_drivers(model['name']):
            if not drv['instance'].is_alive():
                continue
            self.debug('on_model_exit %s', drv['name'])
            if 'onexit' in drv:
                self.debug(drv['onexit'])
                if drv['onexit'] != 'pass':
                    exit_method = getattr(drv['instance'], drv['onexit'])
                    exit_method()
            else:
                drv['instance'].on_model_exit()
    
    def terminate(self):
        r"""Immediately stop all drivers, beginning with IO drivers."""
        self.debug()
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
        self.debug()
        for driver in self.all_drivers:
            if 'instance' in driver:
                driver['instance'].cleanup()

    def printStatus(self):
        r"""Print the status of all drivers, starting with the IO drivers."""
        self.debug()
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
        self.debug()
        drivers = [i for i in self.io_drivers()]
        for drv in drivers:
            if 'instance' in drv:
                driver = drv['instance']
                if driver.is_alive():
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
    os.environ['PSI_RANK'] = rank
    os.environ['PSI_HOST'] = host
    rank = int(rank)
    kwargs.update(rank=rank, host=host)
    # Run
    logger.debug("Running in %s with path %s namespace %s rank %d",
                 os.getcwd(), sys.path, namespace, rank)
    cisRunner = CisRunner(models, namespace, **kwargs)
    return cisRunner
