import os
import unittest
import signal
import uuid
from yggdrasil import runner, tools, platform, import_as_function
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


def test_run_process_connections():
    r"""Test run with process based connections."""
    namespace = "test_run_%s" % str(uuid.uuid4)
    runner.run([ex_yamls['hello']['python']],
               connection_task_method='process',
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


def test_import_as_function():
    r"""Test import_as_function."""
    yamlfile = ex_yamls['fakeplant']['python']
    fmodel = import_as_function(yamlfile)
    input_args = {}
    for x in fmodel.arguments:
        input_args[x] = 1.0
    result = fmodel(**input_args)
    for x in fmodel.returns:
        assert(x in result)
    fmodel.stop()
    fmodel.stop()
            
            
class TestYggRunner(YggTestBase):
    r"""Tests of the YggRunner class."""
    def setup(self, *args, **kwargs):
        super(TestYggRunner, self).setup(*args, **kwargs)
        self.runner = runner.YggRunner([ex_yamls['hello']['python']],
                                       'test_ygg_run')
