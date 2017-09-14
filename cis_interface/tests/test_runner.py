import nose.tools as nt
from cis_interface import runner
from cis_interface.drivers import Driver, ModelDriver, IODriver
from cis_interface.tests import scripts
from cis_interface.examples import yamls


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
    cr = runner.get_runner([yamls['ascii_io']['python']])
    cr.run()

    
def test_runner_terminate():
    r"""Start a runner, then stop it early."""
    cr = runner.get_runner([yamls['ascii_io']['python']])
    cr.loadDrivers()
    cr.startDrivers()
    cr.printStatus()
    cr.terminate()


class TestCisRunner(object):
    r"""Tests of the CisRunner class."""
    def __init__(self):
        nt.assert_raises(IOError, runner.CisRunner,
                         ['fake_yaml.yml'], 'test_psi_run')
        self.runner = runner.CisRunner([yamls['ascii_io']['python']],
                                       'test_psi_run')

    def test_parseModelYaml(self):
        nt.assert_raises(IOError, self.runner.parseModelYaml, 'fake_yaml.yml')
