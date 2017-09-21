"""This module provides tools for running models using cis_interface."""
import importlib
import sys
import logging
from logging import debug, info, error
import os
import yaml
import pystache
from pprint import pformat
from itertools import chain
import socket
from cis_interface.backwards import sio
from cis_interface.config import cis_cfg, cfg_environment
from cis_interface import drivers


COLOR_TRACE = '\033[30;43;22m'
COLOR_NORMAL = '\033[0m'


def setup_cis_logging(prog, level=None):
    r"""Set the log lovel based on environment variable 'PSI_DEBUG'. If the
    variable is not set, the log level is set to 'NOTSET'.

    Args:
        prog (str): Name to prepend log messages with.
        level (str, optional): String specifying the logging level. Defaults
            to None and the environment variable 'PSI_DEBUG' is used.

    """
    if level is None:
        level = cis_cfg.get('debug', 'psi', 'NOTSET')
    logLevel = eval('logging.' + level)
    logging.basicConfig(level=logLevel, stream=sys.stdout, format=COLOR_TRACE +
                        prog + ': %(message)s' + COLOR_NORMAL)

    
def setup_rmq_logging(level=None):
    r"""Set the log level for RabbitMQ to value of environment variable
    'RMQ_DEBUG'. If the variable is not set, the log level is set to 'INFO'.

    Args:
        level (str, optional): String specifying the logging level. Defaults
            to None and the environment variable 'RMQ_DEBUG' is used.

    """
    if level is None:
        level = cis_cfg.get('debug', 'rmq', 'INFO')
    rmqLogLevel = eval('logging.' + level)
    logging.getLogger("pika").setLevel(level=rmqLogLevel)

    
def import_driver(driver):
    r"""Dynamically import a driver based on a string.

    Args:
        driver (str): Name of the driver that should be imported.

    """
    drv = importlib.import_module('cis_interface.drivers.%s' % driver)
    debug("loaded %s", drv)
    class_ = getattr(drv, driver)
    return class_


def create_driver(driver, name, args=None, **kwargs):
    r"""Dynamically create a driver based on a string and other driver
    properties.

    Args:
        driver (str): Name of the driver that should be created.
        name (str): Name to give the driver.
        args (object, optional): Second argument for drivers which take a
            minimum of two arguments. If None, the driver is assumed to take a
            minimum of one argument. Defaults to None.
        \*\*kwargs: Additional keyword arguments are passed to the driver
            class.

    Returns:
        object: Instance of the requested driver.

    """
    class_ = import_driver(driver)
    if args is None:
        instance = class_(name, **kwargs)
    else:
        instance = class_(name, args, **kwargs)
    return instance


class CisRunner(object):
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

    ..todo:: namespace, host, and rank do not seem strictly necessary.

    """
    def __init__(self, modelYmls, namespace, host=None, rank=0,
                 cis_debug_level=None, rmq_debug_level=None,
                 cis_debug_prefix=None):
        self.namespace = namespace
        self.host = host
        self.rank = rank
        self.modeldrivers = {}
        self.inputdrivers = {}
        self.outputdrivers = {}
        self._inputchannels = []
        self._outputchannels = []
        self.error_flag = False
        # Setup logging
        if cis_debug_prefix is None:
            cis_debug_prefix = namespace
        setup_cis_logging(cis_debug_prefix, level=cis_debug_level)
        setup_rmq_logging(level=rmq_debug_level)
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
        info("CisRunner: Loading yaml %s", yamlpath)
        with open(modelYml, 'r') as f:
            try:
                # Mustache replace vars
                yamlparsed = f.read()
                yamlparsed = pystache.render(
                    sio.StringIO(yamlparsed).getvalue(), dict(os.environ))
                yamlparsed = yaml.safe_load(yamlparsed)
                debug("CisRunner: yaml after stache: %s", pformat(yamlparsed))
                # Store parsed models
                yml_models = yamlparsed.get('models', [])
                if 'model' in yamlparsed:
                    yml_models.append(yamlparsed['model'])
                for yml in yml_models:
                    self.add_driver('model', yml, yamldir)
            except Exception as e:  # pragma: debug
                error("CisRunner: could not load yaml: %s: %s", modelYml, e)
                raise  # Nothing started yet so just raise

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
            self._inputchannels.append(yaml['args'])
        elif dtype == 'output':
            dd = self.outputdrivers
            self._outputchannels.append(yaml['args'])
        elif dtype == 'model':
            yaml.setdefault('inputs', [])
            yaml.setdefault('outputs', [])
            # Add server driver
            if yaml.get('is_server', False):
                srv = {'name': yaml['name'],
                       'driver': 'RMQServerDriver',
                       'args': yaml['name']}
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
                           'driver': 'RMQClientDriver',
                           'args': srv}
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

    def run(self):
        r"""Run all of the models and wait for them to exit."""
        self.loadDrivers()
        self.startDrivers()
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
        try:
            debug('creating %s, a %s', yml['name'], yml['driver'])
            curpath = os.getcwd()
            os.chdir(yml['workingDir'])
            instance = create_driver(yml['driver'], yml['name'], yml['args'],
                                     yml=yml, env=yml.get('env', {}),
                                     namespace=self.namespace, rank=self.rank,
                                     workingDir=yml['workingDir'],
                                     **yml['kwargs'])
            yml['instance'] = instance
            os.chdir(curpath)
        except Exception as e:  # pragma: debug
            error("Exception %s: Unable to load driver from yaml %s",
                  e, pformat(yml))
            raise  # Nothing started yet so just raise
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
            debug("CisRunner::loadDrivers: Add env: %s", iod['instance'].env)
            yml['env'].update(iod['instance'].env)
        drv = self.createDriver(yml)
        if 'client_of' in yml:
            for srv in yml['client_of']:
                self.modeldrivers[srv]['clients'].append(yml['name'])
        debug("CisRunner::loadDrivers(): model %s: env: %s",
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
        return drv
        
    def loadDrivers(self):
        r"""Load all of the necessary drivers, doing the IO drivers first
        and adding IO driver environmental variables back tot he models."""
        debug("CisRunner.loadDrivers()")
        # Create input drivers
        debug("CisRunner::loadDrivers(): loading input drivers")
        for driver in self.inputdrivers.values():
            self.createInputDriver(driver)
        # Create output drivers
        debug("CisRunner::loadDrivers(): loading output drivers")
        for driver in self.outputdrivers.values():
            self.createOutputDriver(driver)
        # Create model drivers
        debug("CisRunner::loadDrivers(): loading model drivers")
        for driver in self.modeldrivers.values():
            self.createModelDriver(driver)

    def startDrivers(self):
        r"""Start drivers, starting with the IO drivers."""
        info('Starting I/O drivers and models on system ' +
             '{} in namespace {} with rank {}'.format(
                 self.host, self.namespace, self.rank))
        for driver in self.all_drivers:
            debug("CisRunner.startDrivers(): starting driver %s",
                  driver['name'])
            d = driver['instance']
            try:
                d.start()
            except Exception as e:  # pragma: debug
                error("CisRunner: %s did not start", d.name)
                self.terminate()
                raise e
        debug('CisRunner.startDrivers(): ALL DRIVERS STARTED')

    def waitModels(self):
        r"""Wait for all model drivers to finish. When a model finishes,
        join the thread and perform exits for associated IO drivers."""
        debug('CisRunner:waitDrivers(): ')
        running = [d for d in self.modeldrivers.values()]
        while (len(running) > 0) and (not self.error_flag):
            for drv in running:
                d = drv['instance']
                if d.errors:
                    error('Error in model %s', drv['name'])
                    self.error_flag = True
                    break
                d.join(1)
                if not d.is_alive():
                    self.do_model_exits(drv)
                    running.remove(drv)
                else:
                    info('%s still running', drv['name'])
        for d in self.modeldrivers.values():
            if d['instance'].errors:
                self.error_flag = True
        if not self.error_flag:
            info('All models completed')
        else:
            error('One or more models generated errors.')
            self.terminate()
        debug('RunModels.run() returns')

    def do_exits(self, driver):
        r"""Perform basic exits for a driver.

        Args:
            model (dict): Dictionary of driver parameters.

        """
        debug("CisRunner::do_exits for driver %s", driver['name'])
        # Stop the driver and join the thread
        driver['instance'].on_exit()
        driver['instance'].join()
        debug("CisRunner: join finished: (%s)", pformat(driver))

    def do_model_exits(self, model):
        r"""Perform exists for IO drivers associated with a model.

        Args:
            model (dict): Dictionary of model parameters including any
                associated IO drivers.

        """
        self.do_exits(model)
        # Stop associated server if not more clients
        for srv_name in model.get('client_of', []):
            # Stop client IO driver
            iod = self.outputdrivers["%s_%s" % (srv_name, model['name'])]
            iod['instance'].stop()
            self.do_exits(iod)
            # Remove this client from list for server
            srv = self.modeldrivers[srv_name]
            srv['clients'].remove(model['name'])
            # Stop server if there are not any more clients
            if len(srv['clients']) == 0:
                iod = self.inputdrivers[srv_name]
                iod['instance'].stop()
                self.do_exits(iod)
                srv['instance'].stop()
                # self.do_model_exits(srv)
        # Stop associated IO drivers
        for drv in self.io_drivers(model['name']):
            if not drv['instance'].is_alive():
                continue
            debug('CisRunner::do_model_exits(): on_model_exit %s', drv['name'])
            if 'onexit' in drv:
                debug('CisRunner::onexit: %s', drv['onexit'])
                if drv['onexit'] != 'pass':
                    exit_method = getattr(drv['instance'], drv['onexit'])
                    exit_method()
            else:
                drv['instance'].on_model_exit()
    
    def terminate(self):
        r"""Immediately stop all drivers, beginning with IO drivers."""
        debug('CisRunner::terminate()')
        # self.closeChannels(force_stop=True)
        # debug('CisRunner::terminate(): stop models')
        for driver in self.all_drivers:
            if 'instance' in driver:
                debug('CisRunner::terminate(): stop %s', driver)
                driver['instance'].terminate()
                # Terminate should ensure instance not alive
                assert(not driver['instance'].is_alive())
                # if driver['instance'].is_alive():
                #     driver['instance'].join()
        debug('CisRunner::terminate(): returns')

    def cleanup(self):
        r"""Perform cleanup operations for all drivers."""
        debug('CisRunner::cleanup()')
        for driver in self.all_drivers:
            if 'instance' in driver:
                driver['instance'].cleanup()

    def printStatus(self):
        r"""Print the status of all drivers, starting with the IO drivers."""
        debug("CisRunner: printStatus()")
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
        debug('CisRunner::closeChannels()')
        drivers = [i for i in self.io_drivers()]
        for drv in drivers:
            if 'instance' in drv:
                driver = drv['instance']
                debug("CisRunner:closeChannels(): stopping %s", drv)
                if force_stop or self.error_flag:
                    driver.terminate()
                else:
                    driver.stop()
                debug("CisRunner:closeChannels(): stop(%s) returns", drv)
        debug('closeChannels(): Channel Stops DONE')
        for drv in drivers:
            if 'instance' in drv:
                driver = drv['instance']
                assert(not driver.is_alive())
                # debug("CisRunner:closeChannels: join %s", drv)
                # if driver.is_alive():
                #     driver.join()
                # debug("CisRunner:closeChannels: join %s done", drv)
        debug('CisRunner::closeChannels(): done')

        
def get_runner(models, **kwargs):
    r"""Get runner for a set of models, getting run information from the
    environment.

    Args:
        models (list): List of yaml files containing information on the models
            that should be run.
        \*\*kwargs: Additonal keyword arguments are passed to CisRunner.

    Returns:
        CisRunner: Runner for the provided models.

    Raises:
        Exception: If config option 'namespace' in 'rmq' section not set.

    """
    # Get environment variables
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
    debug("run_models in %s with path %s namespace %s rank %d",
          os.getcwd(), sys.path, namespace, rank)
    cisRunner = CisRunner(models, namespace, **kwargs)
    return cisRunner
