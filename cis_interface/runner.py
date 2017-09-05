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
        level = os.environ.get('PSI_DEBUG', 'NOTSET')
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
        level = os.environ.get('RMQ_DEBUG', 'INFO')
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
        modeldrivers (list): Model drivers associated with this run.
        inputdrivers (list): Input drivers associated with this run.
        outputdrivers (list): Output drivers associated with this run.

    ..todo:: namespace, host, and rank do not seem strictly necessary.

    """
    def __init__(self, modelYmls, namespace, host=None, rank=0,
                 cis_debug_level=None, rmq_debug_level=None,
                 cis_debug_prefix=None):
        self.namespace = namespace
        self.host = host
        self.rank = rank
        self.modeldrivers = []
        self.inputdrivers = []
        self.outputdrivers = []
        # Setup logging
        if cis_debug_prefix is None:
            cis_debug_prefix = namespace
        setup_cis_logging(cis_debug_prefix, level=cis_debug_level)
        setup_rmq_logging(level=rmq_debug_level)
        # Parse yamls
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
                yamlparsed = yaml.safe_load(f)
                yamlparsed = pystache.render(
                    sio.StringIO(yamlparsed).getvalue(), dict(os.environ))
                yamlparsed = yaml.safe_load(yamlparsed)
                debug("CisRunner: yaml after stache: %s", pformat(yamlparsed))
                # Store parsed models
                yml_models = yamlparsed.get('models', [])
                if 'model' in yamlparsed:
                    yml_models.append(yamlparsed['model'])
                for yml in yml_models:
                    yml['workingDir'] = yamldir
                    for inp in yml.get('inputs', dict()):
                        inp['workingDir'] = yamldir
                        self.inputdrivers.append(inp)
                    for inp in yml.get('outputs', dict()):
                        inp['workingDir'] = yamldir
                        self.outputdrivers.append(inp)
                    self.modeldrivers.append(yml)
            except Exception as e:  # pragma: debug
                error("CisRunner:  could not load yaml: %s: %s", modelYml, e)
                raise  # Nothing started yet so just raise

    def run(self):
        r"""Run all of the models and wait for them to exit."""
        self.loadDrivers()
        self.startDrivers()
        self.waitModels()
        self.closeChannels()

    def createDriver(self, yml):
        r"""Create a driver instance from the yaml information.

        Args:
            yml (yaml): Yaml object containing driver information.

        Returns:
            object: An instance of the specified driver.

        """
        debug('creating %s, a %s', yml['name'], yml['driver'])
        instance = create_driver(yml['driver'], yml['name'], yml['args'],
                                 yml=yml, namespace=self.namespace,
                                 rank=self.rank,
                                 workingDir=yml['workingDir'])
        return instance

    def loadDrivers(self):
        r"""Load all of the necessary drivers, doing the IO drivers first
        and adding IO driver environmental variables back tot he models."""
        debug("CisRunner.loadDrivers()")
        # Create all of the drivers
        for driver in [i for i in chain(
                self.outputdrivers, self.inputdrivers, self.modeldrivers)]:
            debug("RunModels.loaDrivers(): loading driver %s", pformat(driver))
            try:
                curpath = os.getcwd()
                os.chdir(driver['workingDir'])
                drv = self.createDriver(driver)
                driver['instance'] = drv
                os.chdir(curpath)
            except Exception as e:  # pragma: debug
                info("ERROR:  Exception %s: Unable to load driver from yaml %s",
                     e, pformat(driver))
                raise  # Nothing started yet so just raise
        # Add the env's from the IO drivers to the models to ensure that
        # they have access to the necessary queues
        for driver in self.modeldrivers:
            debug("CisRunner::loadDrivers: driver %s", driver)
            iodrivers = [i for i in chain(driver.get('inputs', dict()),
                                          driver.get('outputs', dict()))]
            modelenv = driver['instance'].env
            modelenv.update(os.environ)
            for iod in iodrivers:
                debug("PSrRun::loadDrivers:  Add env: %s", iod['instance'].env)
                modelenv.update(iod['instance'].env)
            debug("CisRunner::loadDrivers(): model %s: env: %s",
                  driver['name'], pformat(driver['instance'].env))

    def startDrivers(self):
        r"""Start drivers, starting with the IO drivers."""
        info('Starting I/O drivers and models on system ' +
             '{} in PSI_NAMESPACE {} PSI_RANK {}'.format(
                 self.host, self.namespace, self.rank))
        for driver in [i for i in chain(self.outputdrivers, self.inputdrivers,
                                        self.modeldrivers)]:
            debug("RunModels.startDrivers(): starting driver %s",
                  driver['name'])
            d = driver['instance']
            try:
                d.start()
            except Exception as e:  # pragma: debug
                error("CisRunner:  ERROR:  %s did not start", d.name)
                raise e
        debug('CisRunner(): ALL DRIVERS STARTED')

    def waitModels(self):
        r"""Wait for all model drivers to finish. When a model finishes,
        join the thread and perform exits for associated IO drivers."""
        debug('CisRunner:waitDrivers(): ')
        running = [d for d in self.modeldrivers]
        while(len(running)):
            for drv in running:
                d = drv['instance']
                d.join(1)
                if not d.is_alive():
                    self.do_exits(drv)
                    running.remove(drv)
        # self.closeChannels()
        info('All models completed')
        debug('RunModels.run() returns')

    def do_exits(self, model):
        r"""Perform exists for IO drivers associated with a model.

        Args:
            model (dict): Dictionary of model parameters including any
                associated IO drivers.

        """
        debug("CisRunner::do_exits for model %s", model['name'])
        # Stop the model and join the thread
        model['instance'].on_exit()
        model['instance'].join()
        debug("CisRunner: join finished: (%s)", pformat(model))
        # Stop associated IO drivers
        iodrivers = [i for i in chain(model.get('inputs', dict()),
                                      model.get('outputs', dict()))]
        for drv in iodrivers:
            debug('CisRunner::do_exits(): delete %s', drv['name'])
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
        self.closeChannels(force_stop=True)
        debug('CisRunner::terminate(): stop models')
        for driver in chain(self.outputdrivers, self.inputdrivers,
                            self.modeldrivers):
            debug('CisRunner::terminate(): stop %s', driver)
            driver['instance'].stop()
        debug('CisRunner::terminate(): returns')

    def printStatus(self):
        r"""Print the status of all drivers, starting with the IO drivers."""
        debug("CisRunner: printStatus()")
        for driver in chain(self.inputdrivers, self.outputdrivers,
                            self.modeldrivers):
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
        drivers = [i for i in chain(self.outputdrivers, self.inputdrivers)]
        for driver in drivers:
            driver = driver['instance']
            debug("CisRunner:closeChannels(): stopping %s", driver)
            if force_stop:
                driver.terminate()
            else:
                driver.stop()
            debug("CisRunner:closeChannels(): stop(%s) returns", driver)
        debug('closeChannels(): Channel Stops DONE')
        for driver in drivers:
            driver = driver['instance']
            debug("CisRunner:closeChannels: join %s", driver)
            driver.join()
            debug("CisRunner:closeChannels: join %s done", driver)
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
        Exception: If environment variable 'PSI_NAMESPACE' is not set.

    """
    # Get environment variables
    namespace = os.environ.get('PSI_NAMESPACE', False)
    if not namespace:  # pragma: debug
        raise Exception('PSI_NAMESPACE not set')
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
