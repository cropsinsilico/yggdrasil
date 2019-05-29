import os
import unittest
import logging
from yggdrasil.tests import scripts, assert_raises
import yggdrasil.drivers.tests.test_InterpretedModelDriver as parent
from yggdrasil import runner
from yggdrasil.drivers import MatlabModelDriver
from yggdrasil.examples import yamls as ex_yamls


logger = logging.getLogger(__name__)
_session_fname = os.path.join(os.getcwd(), 'nt_screen_session.txt')


def test_is_matlab_running():
    r"""Test if there is Matlab engine running."""
    MatlabModelDriver.is_matlab_running()
    MatlabModelDriver.kill_all()
    assert(not MatlabModelDriver.is_matlab_running())


@unittest.skipIf(MatlabModelDriver.MatlabModelDriver.is_installed(),
                 "Matlab installed.")
def test_matlab_not_installed():  # pragma: no matlab
    r"""Assert that errors are raised when Matlab is not installed."""
    assert_raises(RuntimeError, MatlabModelDriver.start_matlab_engine)
    assert_raises(RuntimeError, MatlabModelDriver.stop_matlab_engine,
                  None, None, None, None)
    assert_raises(RuntimeError, MatlabModelDriver.MatlabProcess, None, None)
    assert_raises(RuntimeError, MatlabModelDriver.MatlabModelDriver, None, None)


@unittest.skipIf(not MatlabModelDriver.MatlabModelDriver.is_installed(),
                 "Matlab not installed.")
def test_matlab_runner():  # pragma: matlab
    r"""Use get_runner to start a Matlab run."""
    cr = runner.get_runner([ex_yamls['hello']['matlab']])
    cr.run()


@unittest.skipIf(not MatlabModelDriver.MatlabModelDriver.is_installed(),
                 "Matlab not installed.")
def test_matlab_exit():  # pragma: matlab
    r"""Test error when model contains 'exit' call."""
    MatlabModelDriver.MatlabModelDriver('error', [scripts['matlab_error']])
    # Re-enable if it becomes necessary to raise an error instead of just a warning
    # assert_raises(RuntimeError, MatlabModelDriver.MatlabModelDriver, 'error',
    #                  [scripts['matlab_error']])


@unittest.skipIf(not MatlabModelDriver.MatlabModelDriver.is_installed(),
                 "Matlab not installed.")
def test_locate_matlabroot():  # pragma: matlab
    r"""Test locate_matlabroot."""
    MatlabModelDriver.locate_matlabroot()


class TestMatlabModelParam(parent.TestInterpretedModelParam):  # pragma: matlab
    r"""Test parameters for MatlabModelDriver."""

    driver = "MatlabModelDriver"
    
    def __init__(self, *args, **kwargs):
        super(TestMatlabModelParam, self).__init__(*args, **kwargs)
        self.args = [self.src[0], "test", 1]
        self.attr_list += ['started_matlab', 'mlengine']

            
class TestMatlabModelDriverNoInit(TestMatlabModelParam,  # pragma: matlab
                                  parent.TestInterpretedModelDriverNoInit):
    r"""Test runner for MatlabModelDriver without instance."""
    pass


class TestMatlabModelDriverNoStart(TestMatlabModelParam,  # pragma: matlab
                                   parent.TestInterpretedModelDriverNoStart):
    r"""Test runner for MatlabModelDriver without starting the driver."""
    pass


class TestMatlabModelDriver(TestMatlabModelParam,
                            parent.TestInterpretedModelDriver):  # pragma: matlab
    r"""Test runner for MatlabModelDriver."""
    
    @unittest.skipIf(not MatlabModelDriver._matlab_engine_installed,
                     "Matlab engine not installed.")
    def test_a(self):
        r"""Dummy test to start matlab."""
        if self.instance.screen_session is None:  # pragma: debug
            logger.info("Matlab was not started by this test. Close any "
                        + "existing Matlab sessions to test creation/removal.")
        else:
            with open(_session_fname, 'w') as f:
                f.write(self.instance.screen_session)
            self.instance.screen_session = None
            self.instance.started_matlab = False

    @unittest.skipIf(not MatlabModelDriver._matlab_engine_installed,
                     "Matlab engine not installed.")
    def test_z(self):
        r"""Dummy test to stop matlab."""
        if os.path.isfile(_session_fname):
            with open(_session_fname, 'r') as f:
                session = f.read()
            os.remove(_session_fname)
            self.instance.screen_session = session
            self.instance.started_matlab = True
        else:  # pragma: debug
            logger.info("Skipping removal of Matlab session as the test did "
                        + "not create it.")
