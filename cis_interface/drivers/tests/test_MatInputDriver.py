import os
import numpy as np
from scipy.io import savemat
from cis_interface.backwards import pickle
import cis_interface.drivers.tests.test_IODriver as parent


class TestMatInputDriver(parent.TestIODriver):
    r"""Test runner for MatInputDriver.

    Attributes (in addition to parent class's):
        filepath (str): Full path to test file.
    
    """

    def __init__(self, *args, **kwargs):
        super(TestMatInputDriver, self).__init__(*args, **kwargs)
        self.driver = 'MatInputDriver'
        self.filepath = os.path.abspath('mat_input.mat')
        self.args = self.filepath
        # self.timeout = 60.0

    def setup(self):
        r"""Create a driver instance and start the driver."""
        with open(self.filepath, 'wb') as fd:
            savemat(fd, self.data_dict)
        super(TestMatInputDriver, self).setup()

    def teardown(self):
        r"""Remove the instance, stoppping it."""
        super(TestMatInputDriver, self).teardown()
        if os.path.isfile(self.filepath):
            os.remove(self.filepath)

    def assert_before_stop(self):
        r"""Assertions to make before stopping the driver instance."""
        super(TestMatInputDriver, self).assert_before_stop()
        msg_recv = self.instance.recv_wait_nolimit()
        assert(msg_recv)
        dat_recv = pickle.loads(msg_recv)
        for k in self.data_dict.keys():
            np.testing.assert_array_equal(dat_recv[k], self.data_dict[k])

    def assert_after_terminate(self):
        r"""Assertions to make after stopping the driver instance."""
        super(TestMatInputDriver, self).assert_after_terminate()
        assert(self.instance.fd is None)

    def test_send_recv(self):
        r"""Test sending/receiving small message."""
        pass

    def test_send_recv_nolimit(self):
        r"""Test sending/receiving large message."""
        pass
