import pytest
import os
import logging
from yggdrasil import runner
from yggdrasil.drivers import MatlabModelDriver
from yggdrasil.examples import yamls as ex_yamls
from tests.drivers.test_ModelDriver import TestModelDriver as base_class


logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def matlab_session_file():
    return os.path.join(os.getcwd(), 'nt_screen_session.txt')


@pytest.mark.related_language('matlab')
def test_is_matlab_running():
    r"""Test if there is Matlab engine running."""
    MatlabModelDriver.is_matlab_running()
    MatlabModelDriver.kill_all()
    assert(not MatlabModelDriver.is_matlab_running())


@pytest.mark.skipif(MatlabModelDriver._matlab_engine_installed,
                    reason="Matlab installed.")
def test_matlab_engine_not_installed():  # pragma: no matlab
    r"""Assert that errors are raised when Matlab engine is not installed."""
    with pytest.raises(RuntimeError):
        MatlabModelDriver.start_matlab_engine()
    with pytest.raises(RuntimeError):
        MatlabModelDriver.stop_matlab_engine(None, None, None, None)
    with pytest.raises(RuntimeError):
        MatlabModelDriver.MatlabProcess(None, None)


@pytest.mark.language('matlab')
def test_matlab_runner():  # pragma: matlab
    r"""Use get_runner to start a Matlab run."""
    cr = runner.get_runner([ex_yamls['hello']['matlab']])
    cr.run()


@pytest.mark.language('matlab')
def test_matlab_exit(scripts):  # pragma: matlab
    r"""Test error when model contains 'exit' call."""
    MatlabModelDriver.MatlabModelDriver('error', [scripts['matlab_error']])
    # Re-enable if it becomes necessary to raise an error instead of just a warning
    # with pytest.raises(RuntimeError):
    #     MatlabModelDriver.MatlabModelDriver('error', [scripts['matlab_error']])


@pytest.mark.language('matlab')
def test_locate_matlabroot():  # pragma: matlab
    r"""Test locate_matlabroot."""
    MatlabModelDriver.locate_matlabroot()


class TestMatlabModelDriver(base_class):  # pragma: matlab
    r"""Test parameters for MatlabModelDriver."""

    @pytest.fixture(scope="class")
    def language(self):
        r"""str: Language being tested."""
        return 'matlab'

    # @pytest.fixture(autouse=True)
    # def record_screen_session(self, instance, matlab_session_file):
    #     r"""Write the screen session to a file."""
    #     if instance.screen_session is None:  # pragma: debug
    #         logger.info("Matlab was not started by this test. Close any "
    #                     "existing Matlab sessions to test creation/removal.")
    #     else:
    #         with open(matlab_session_file, 'w') as f:
    #             f.write(instance.screen_session)
    #         instance.screen_session = None
    #         instance.started_matlab = False

    # @pytest.mark.skipif(not MatlabModelDriver._matlab_engine_installed,
    #                     reason="Matlab engine not installed.")
    # def test_z(self, instance, matlab_session_file):
    #     r"""Dummy test to stop matlab."""
    #     if os.path.isfile(matlab_session_file):
    #         with open(matlab_session_file, 'r') as f:
    #             session = f.read()
    #         os.remove(matlab_session_file)
    #         instance.screen_session = session
    #         instance.started_matlab = True
    #     else:  # pragma: debug
    #         logger.info("Skipping removal of Matlab session as the test did "
    #                     "not create it.")
