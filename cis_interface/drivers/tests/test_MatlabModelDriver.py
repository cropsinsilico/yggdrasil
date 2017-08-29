import os
import test_ModelDriver as parent


_session_fname = os.path.join(os.getcwd(), 'nt_screen_session.txt')

class TestMatlabModelDriver(parent.TestModelDriver):
    r"""Test runner for MatlabModelDriver."""

    def __init__(self):
        super(TestMatlabModelDriver, self).__init__()
        self.driver = "MatlabModelDriver"
        self.args = ["matlab_model.m", "test", 1]
        self.attr_list += ['started_matlab', 'mlengine']

    def test_a(self):
        r"""Dummy test to start matlab."""
        if self.instance.screen_session is None:  # pragma: debug
            print("Matlab was not started by this test. Close any " +
                  "existing Matlab sessions to test creation/removal.")
        else:
            with open(_session_fname, 'w') as f:
                f.write(self.instance.screen_session)
            self.instance.screen_session = None
            self.instance.started_matlab = False

    def test_z(self):
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
