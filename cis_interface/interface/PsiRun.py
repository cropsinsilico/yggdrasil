#!/usr/bin/python

import importlib
import sys
import time
import logging
from logging import *
import signal
import os
import yaml
import pystache
from StringIO import StringIO
import uuid
import traceback
from pprint import pformat
from itertools import chain
import socket

psiRunner = None
INTERRUPT_TIME = 0
COLOR_TRACE = '\033[30;43;22m'
COLOR_NORMAL = '\033[0m'


## pretty pprint
def pprint(*args):
    s = ''.join(str(i) for i in args)
    print COLOR_TRACE+'{}'+COLOR_NORMAL.format(s)

    
def import_driver(driver):
    # from pycis import drivers
    # drv = getattr(drivers, driver)
    # debug("loaded %s", drv)
    # class_ = getattr(drv, driver)
    # class_ = importlib.import_module('pycis.drivers.%s.%s' % (driver, driver))
    drv = importlib.import_module('pycis.drivers.%s' % driver)
    debug("loaded %s", drv)
    class_ = getattr(drv, driver)
    return class_


def create_driver(driver, name, args = None, **kwargs):
    class_ = import_driver(driver)
    if args is None:
        instance = class_(name, **kwargs)
    else:
        instance = class_(name, args, **kwargs)
    return instance


class PsiRun(object):
    def __init__(self, modelYmls, host, namespace, rank):
        self.namespace = namespace
        self.rank = rank
        self.host = host
        self.models = []
        self.modeldrivers = []
        self.inputdrivers = []
        self.outputdrivers = []
        for modelYml in modelYmls:
            yamlpath = os.path.realpath(modelYml)
            yamldir = os.path.dirname(yamlpath)
            if not os.path.isfile(yamlpath):
                error('PsiRun(): File error: unable to locate %s' % yamlpath)
                exit(-1)
            info("psirun: Loading yaml %s", yamlpath)
            # open each yaml, get full path, mustache replace vars, store it
            with open(modelYml, 'r') as f:
                try:
                    yamlparsed = yaml.safe_load(f)
                    yamlparsed = pystache.render(StringIO(yamlparsed).getvalue(), dict(os.environ))
                    yamlparsed = yaml.safe_load(yamlparsed)
                    debug("PsiRun: yaml after stache: %s", pformat(yamlparsed))
                    if 'models' in yamlparsed:
                        for yml in yamlparsed['models']:
                            self.parseModelYaml(yml, yamldir)
                    if 'model' in yamlparsed:
                        self.parseModelYaml(yamlparsed['model'], yamldir)
                except Exception as e:
                    error("psirun:  could not load yaml: %s: %s", modelYml, e)
                    raise # Nothing started yet so just raise
                    sys.exit(-1)
        #print pformat(self.inputdrivers), pformat(self.outputdrivers), pformat(self.modeldrivers)
        debug("PsiRun():: models \n%s", pformat(self.models))
        return

    def parseModelYaml(self, yml, yamldir):
        yml['workingDir'] = yamldir
        for inp in yml.get('inputs', dict()):
            inp['workingDir'] = yamldir
            self.inputdrivers.append(inp)
        for inp in yml.get('outputs', dict()):
            inp['workingDir'] = yamldir
            self.outputdrivers.append(inp)
        self.modeldrivers.append(yml)

    def createDriver(self, yml):
        debug('creating %s, a %s', yml['name'], yml['driver'])
        instance = create_driver(yml['driver'], yml['name'], yml['args'],
                                 yml=yml, namespace=self.namespace,
                                 rank=self.rank,
                                 workingDir=yml['workingDir'])
        # instance.yml = yml
        # instance.namespace = self.namespace
        # instance.rank = self.rank
        # instance.workingDir = yml['workingDir']
        return instance

    def loadDrivers(self):
        debug("PsiRun.loadDrivers()")
        # All drivers: create
        for driver in [i for i in chain(self.outputdrivers, self.inputdrivers, \
            self.modeldrivers)]:
            debug("RunModels.loaDrivers(): loading driver %s", pformat(driver))
            try:
                curpath = os.getcwd()
                os.chdir(driver['workingDir'])
                drv = self.createDriver(driver)
                driver['instance'] = drv
                os.chdir(curpath)
            except Exception as e:
                info("ERROR:  Exception %s: Unable to load driver from yaml %s", e, \
                pformat(driver))
                traceback.print_exc()
                sys.exit(-1)

        # Models - add the env's from the IO's to the models
        for driver in self.modeldrivers:
            debug("PsiRun::loadDrivers: driver %s", driver)
            iodrivers = [i for i in chain(\
                driver.get('inputs', dict()), \
                driver.get('outputs', dict()))]
            modelenv = driver['instance'].env
            modelenv.update(os.environ)
            for iod in iodrivers:
                debug("PSrRun::loadDrivers:  Add env: %s", iod['instance'].env)
                modelenv.update(iod['instance'].env)
            debug("PsiRun::loadDrivers(): model %s: env: %s", driver['name'], \
                pformat(driver['instance'].env))
        return

    def startDrivers(self):
        info('Starting I/O drivers and models on system {} in PSI_NAMESPACE {} PSI_RANK {}'.format( \
            socket.gethostname(), self.namespace, self.rank))
        for driver in [i for i in chain(self.outputdrivers, self.inputdrivers, self.modeldrivers)]:
            debug("RunModels.startDrivers(): starting driver %s", driver['name'])
            d = driver['instance']
            try:
                d.start()
            except Exception as e:
                error("psirun:  ERROR:  %s did not start", d.name)
                raise e
        debug('PsiRun(): ALL DRIVERS STARTED')
        return

    def waitModels(self):
        debug('PSiRun:waitDrivers(): ')
        running = [d for d in self.modeldrivers]
        while(len(running)):
            for drv in running:
                d = drv['instance']
                d.join(1)
                if not d.is_alive():
                    d.join()
                    running.remove(drv)
                    debug("PsiRun: join finished: (%s)", pformat(drv))
                    self.do_exits(drv)
        #self.closeChannels()
        info('All models completed')
        debug('RunModels.run() returns')

    def do_exits(self, model):
        debug("PsiRun::do_exits for model %s", model['name'])
        iodrivers = [i for i in chain(\
                model.get('inputs', dict()), \
                model.get('outputs', dict()))]
        for drv in iodrivers:
            debug('PsiRun::do_exits(): delete %s', drv['name'])
            drv['instance'].on_delete()
            # if 'onexit' in drv:
            #     debug('PsiRun::onexit: %s', drv['onexit'])
            #     if drv['onexit'] == 'delete':
            #         debug('PsiRun::do_exits(): stop %s"', drv['name'])
            #         drv['instance'].delete()
    
    def terminate(self):
        debug('PsiRun::terminate()')
        self.closeChannels(force_stop=True)
        debug('PsiRun::terminate(): stop models')
        for driver in chain(self.outputdrivers, self.inputdrivers, self.modeldrivers):
            debug('PsiRun::terminate(): stop %s', driver)
            driver['instance'].stop()
        debug('PsiRun::terminate(): returns')

    def printStatus(self):
        debug("PsiRun: printStatus()")
        for driver in chain(self.inputdrivers, self.outputdrivers, self.modeldrivers):
            driver['instance'].printStatus()

    def closeChannels(self, force_stop=False):
        debug('PsiRun::closeChannels()')
        drivers = [i for i in chain(self.outputdrivers, self.inputdrivers)]
        for driver in drivers:
            driver = driver['instance']
            debug("PsiRun:closeChannels(): stopping %s", driver)
            if force_stop:
                driver.terminate()
            else:
                driver.stop()
            debug("PsiRun:closeChannels(): stop(%s) returns", driver)
        debug('closeChannels(): Channel Stops DONE')
        for driver in drivers:
            driver = driver['instance']
            debug("PsiRun:closeChannels: join %s", driver)
            driver.join()
            debug("PsiRun:closeChannels: join %s done", driver)
        debug('PsiRun::closeChannels(): done')

def setup_psi_logging(prog):
    r"""Set the log lovel based on environment variable 'PSI_DEBUG'. If the
    variable is not set, the log level is set to 'NOTSET'.

    Args:
        prog (str): Name to prepend log messages with.

    """
    logLevel = eval('logging.'+os.environ.get('PSI_DEBUG', 'NOTSET'))
    logging.basicConfig(level=logLevel, stream=sys.stdout, format=COLOR_TRACE + \
        prog + ': %(message)s' + COLOR_NORMAL)

def setup_rmq_logging():
    r"""Set the log level for RabbitMQ to value of environment variable
    'RMQ_DEBUG'. If the variable is not set, the log level is set to 'INFO'."""
    rmqLogLevel = eval('logging.'+os.environ.get('RMQ_DEBUG', 'INFO'))
    logging.getLogger("pika").setLevel(level=rmqLogLevel)

def main(models):
    global psiRunner
    prog = sys.argv[0].split('/')[-1]

    # Setup logging
    setup_psi_logging(prog)
    setup_rmq_logging()

    # Get environment variables
    namespace = os.environ.get('PSI_NAMESPACE', False)
    if not namespace:
        print 'ERROR: PSI_NAMESPACE not set'
	exit(-1)
    rank = os.environ.get('PARALLEL_SEQ', '0')
    os.environ['PSI_RANK'] = rank
    rank = int(rank)
    host = socket.gethostname()
    os.environ['PSI_HOST'] = host

    # Run
    debug("PsiRun in %s with path %s namespace %s rank %d", os.getcwd(), sys.path, namespace, rank)
    psiRunner = PsiRun(models, host, namespace, rank)
    psiRunner.loadDrivers()
    psiRunner.startDrivers()
    psiRunner.waitModels()
    psiRunner.closeChannels()
    return

def signal_handler(sigCaught, frame):
    global INTERRUPT_TIME, psiRunner
    debug('PsiRun interrupted with signal %d', sigCaught)
    now = time.time()
    elapsed = now-INTERRUPT_TIME
    debug('PsiRun.handler: elapsed since last interrupt: %d', elapsed)
    INTERRUPT_TIME = now
    if elapsed < 5:
        pprint(' ')
        pprint('*********************************************************')
        pprint('*  Interrupted twice within 5 seconds:  shutting down   *')
        pprint('*********************************************************')
        #signal.siginterrupt(signal.SIGTERM, True)
        #signal.siginterrupt(signal.SIGINT, True)
        debug("PsiRun.closing all channels")
        if psiRunner:
            psiRunner.terminate()
        #os.popen('/usr/bin/ipcrm --all=msg')
        #os.popen('/usr/bin/reset')
        return 1
    else:
        pprint('')
        pprint('*********************************************************')
        pprint('*  Interrupted: Displaying channel summary              *')
        pprint('*  interrupt again (within 5 seconds) to exit           *')
        pprint('*********************************************************')
        if psiRunner:
            psiRunner.printStatus()
        pprint('*********************************************************')
    debug('PsiRun handler(%d) returns', sigCaught)
    return 0

if __name__ == '__main__':
    try:
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        signal.siginterrupt(signal.SIGTERM, False)
        signal.siginterrupt(signal.SIGINT, False)
        main(sys.argv[1:])
        debug("main returns, exiting")
    except Exception as ex:
        pprint("psirun: exception: %s" % type(ex))
        print(traceback.format_exc())
    print ''
    sys.exit(0)
