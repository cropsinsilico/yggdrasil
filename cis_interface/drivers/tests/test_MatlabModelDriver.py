import os
from cis_interface.tests import scripts
import cis_interface.drivers.tests.test_ModelDriver as parent
from cis_interface import runner
# from cis_interface.drivers.MatlabModelDriver import _matlab_installed
from cis_interface.examples import yamls as ex_yamls


_session_fname = os.path.join(os.getcwd(), 'nt_screen_session.txt')


def test_matlab_runner():
    r"""Use get_runner to start a Matlab run."""
    cr = runner.get_runner([ex_yamls['hello']['matlab']])
    cr.run()


class TestMatlabModelDriver(parent.TestModelDriver,
                            parent.TestModelDriverNoStart):
    r"""Test runner for MatlabModelDriver.

    Attributes (in addition to parent class's):
        -

    """

    def __init__(self, *args, **kwargs):
        super(TestMatlabModelDriver, self).__init__(*args, **kwargs)
        self.driver = "MatlabModelDriver"
        self.args = [scripts["matlab"], "test", 1]
        self.attr_list += ['started_matlab', 'mlengine']

    def test_a(self):  # pragma: matlab
        r"""Dummy test to start matlab."""
        if self.instance.screen_session is None:  # pragma: debug
            print("Matlab was not started by this test. Close any " +
                  "existing Matlab sessions to test creation/removal.")
        else:
            with open(_session_fname, 'w') as f:
                f.write(self.instance.screen_session)
            self.instance.screen_session = None
            self.instance.started_matlab = False

    def test_z(self):  # pragma: matlab
        r"""Dummy test to stop matlab."""
        if os.path.isfile(_session_fname):
            with open(_session_fname, 'r') as f:
                session = f.read()
            os.remove(_session_fname)
            self.instance.screen_session = session
            self.instance.started_matlab = True
        else:  # pragma: debug
            print("Skipping removal of Matlab session as the test did " +
                  "not create it.")
