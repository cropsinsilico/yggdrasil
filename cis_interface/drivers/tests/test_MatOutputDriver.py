import os
import numpy as np
from scipy.io import loadmat
import cis_interface.drivers.tests.test_IODriver as parent


class TestMatOutputParam(parent.TestIOParam):
    r"""Test parameters for MatOutputDriver.

    Attributes (in addition to parent class's):
        filepath (str): Full path to test file.
    
    """

    def __init__(self, *args, **kwargs):
        super(TestMatOutputParam, self).__init__(*args, **kwargs)
        self.driver = 'MatOutputDriver'
        self.filepath = os.path.abspath('mat_input.mat')
        self.args = self.filepath
        

class TestMatOutputDriverNoStart(TestMatOutputParam,
                                 parent.TestIODriverNoStart):
    r"""Test runner for MatOutputDriver.

    Attributes (in addition to parent class's):
        -
    
    """
    pass


class TestMatOutputDriver(TestMatOutputParam, parent.TestIODriver):
    r"""Test runner for MatOutputDriver.

    Attributes (in addition to parent class's):
        -
    
    """

    def setup(self):
        r"""Create a driver instance and start the driver."""
        super(TestMatOutputDriver, self).setup()
        self.instance.ipc_send_nolimit(self.pickled_data)
        self.instance.ipc_send_nolimit(self.instance.eof_msg)
        # self.timeout = 10.0

    def teardown(self):
        r"""Remove the instance, stoppping it."""
        super(TestMatOutputDriver, self).teardown()
        if os.path.isfile(self.filepath):
            os.remove(self.filepath)

    def assert_after_stop(self):
        r"""Assertions to make after stopping the driver instance."""
        super(TestMatOutputDriver, self).assert_after_stop()
        assert(os.path.isfile(self.filepath))
        with open(self.filepath, 'rb') as fd:
            dat_recv = loadmat(fd)
        for k in self.data_dict.keys():
            np.testing.assert_array_equal(dat_recv[k], self.data_dict[k])

    def assert_after_terminate(self):
        r"""Assertions to make after stopping the driver instance."""
        super(TestMatOutputDriver, self).assert_after_terminate()
        assert(self.instance.fd is None)

    # These are disabled to prevent writting extraneous data
    def test_send_recv(self):
        r"""Test sending/receiving small message."""
        pass

    def test_send_recv_nolimit(self):
        r"""Test sending/receiving large message."""
        pass

    def run_before_terminate(self):
        r"""Commands to run while the instance is running, before terminate."""
        pass
