import os
import unittest
import signal
import uuid
from yggdrasil import runner, tools, platform
from yggdrasil.tests import YggTestBase, assert_raises
# from yggdrasil.tests import yamls as sc_yamls
from yggdrasil.examples import yamls as ex_yamls


def test_get_runner():
    r"""Use get_runner to start a run."""
    namespace = "test_get_runner_%s" % str(uuid.uuid4)
    cr = runner.get_runner([ex_yamls['hello']['python']],
                           namespace=namespace)
    cr.run()
    cr.sleep()


def test_get_run():
    r"""Use run function to start a run."""
    namespace = "test_run_%s" % str(uuid.uuid4)
    runner.run([ex_yamls['hello']['python']],
               namespace=namespace)
    runner.run([ex_yamls['model_error']['python']],
               namespace=namespace)


# def test_runner_error():
#     r"""Start a runner for a model with an error."""
#     cr = runner.get_runner([sc_yamls['error']])
#     cr.run()


# Spawning fake Ctrl-C works locally for windows, but causes hang on appveyor
@unittest.skipIf(platform._is_win, "Signal processing not sorted on windows")
def test_Arunner_interrupt():
    r"""Start a runner then stop it with a keyboard interrupt."""
    cr = runner.get_runner([ex_yamls['hello']['python']])
    if platform._is_win:  # pragma: debug
        cr.debug_log()
    cr.loadDrivers()
    cr.startDrivers()
    cr.set_signal_handler()
    tools.kill(os.getpid(), signal.SIGINT)
    tools.kill(os.getpid(), signal.SIGINT)
    cr.reset_signal_handler()
    cr.waitModels()
    cr.closeChannels()
    cr.cleanup()
    if platform._is_win:  # pragma: debug
        cr.reset_log()


def test_runner_terminate():
    r"""Start a runner, then stop it early."""
    cr = runner.get_runner([ex_yamls['hello']['python']])
    cr.loadDrivers()
    cr.startDrivers()
    cr.printStatus()
    cr.terminate()


def test_runner_error():
    r"""Test error on missing yaml."""
    assert_raises(IOError, runner.YggRunner,
                  ['fake_yaml.yml'], 'test_ygg_run')
    

class TestYggRunner(YggTestBase):
    r"""Tests of the YggRunner class."""
    def setup(self, *args, **kwargs):
        super(TestYggRunner, self).setup(*args, **kwargs)
        self.runner = runner.YggRunner([ex_yamls['hello']['python']],
                                       'test_ygg_run')

    def test_createIODriver(self):
        r"""Test createInputDriver and createOutputDriver."""
        yml = {'name': 'fake_IODriver',
               'args': 'fake_channel',
               'driver': 'InputDriver',
               'working_dir': os.getcwd(),
               'icomm_kws': {'comm': [{'name': 'fake_IODriver'}]},
               'ocomm_kws': {'comm': [{'name': 'fake_IODriver'}]},
               'kwargs': {}}
        assert_raises(Exception, self.runner.createInputDriver, yml)
        yml['driver'] = 'OutputDriver'
        assert_raises(Exception, self.runner.createOutputDriver, yml)
