import os
import nose.tools as nt
from cis_interface import runner
from cis_interface.drivers import Driver, ModelDriver, IODriver
from cis_interface.tests import scripts
from cis_interface.tests import yamls as sc_yamls
from cis_interface.examples import yamls as ex_yamls


def test_import_driver():
    r"""Check a few drivers."""
    drvs = [('Driver', Driver.Driver),
            ('ModelDriver', ModelDriver.ModelDriver),
            ('IODriver', IODriver.IODriver)]
    for n, dans in drvs:
        dres = runner.import_driver(n)
        nt.assert_equal(dres, dans)


def test_create_driver():
    r"""Test driver creation w/ and w/o args."""
    runner.create_driver('Driver', 'test_io_driver')
    runner.create_driver('ModelDriver', 'test_model_driver',
                         args=scripts['python'])


def test_get_runner():
    r"""Use get_runner to start a run."""
    cr = runner.get_runner([ex_yamls['hello']['python']])
    cr.run()


def test_runner_error():
    r"""Start a runner for a model with an error."""
    cr = runner.get_runner([sc_yamls['error']])
    cr.run()
    
    
def test_runner_terminate():
    r"""Start a runner, then stop it early."""
    cr = runner.get_runner([ex_yamls['hello']['python']])
    cr.loadDrivers()
    cr.startDrivers()
    cr.printStatus()
    cr.terminate()


class TestCisRunner(object):
    r"""Tests of the CisRunner class."""
    def __init__(self):
        nt.assert_raises(IOError, runner.CisRunner,
                         ['fake_yaml.yml'], 'test_psi_run')
        self.runner = runner.CisRunner([ex_yamls['hello']['python']],
                                       'test_psi_run')

    def test_parseModelYaml(self):
        r"""Test parseModelYaml."""
        nt.assert_raises(IOError, self.runner.parseModelYaml, 'fake_yaml.yml')

    def test_add_driver(self):
        r"""Test add_driver."""
        nt.assert_raises(ValueError, self.runner.add_driver, 'fake_type', {}, '')
        xname = list(self.runner.inputdrivers.keys())[0]
        x = self.runner.inputdrivers[xname]
        nt.assert_raises(ValueError, self.runner.add_driver, 'input', x,
                         x['workingDir'])
        x = self.runner.inputdrivers.pop(xname)
        x['kwargs'] = {}
        nt.assert_raises(RuntimeError, self.runner.add_driver, 'input', x,
                         x['workingDir'])

    def test_createIODriver(self):
        r"""Test createInputDriver and createOutputDriver."""
        yml = {'name': 'fake_IODriver',
               'args': 'fake_channel',
               'driver': 'RMQInputDriver',
               'workingDir': os.getcwd(),
               'kwargs': {}}
        nt.assert_raises(Exception, self.runner.createInputDriver, yml)
        yml['driver'] = 'RMQOutputDriver'
        nt.assert_raises(Exception, self.runner.createOutputDriver, yml)
