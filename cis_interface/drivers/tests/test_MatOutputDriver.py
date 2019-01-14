import os
import cis_interface.drivers.tests.test_FileOutputDriver as parent


class TestMatOutputParam(parent.TestFileOutputParam):
    r"""Test parameters for MatOutputDriver."""

    ocomm_name = 'MatFileComm'
        

class TestMatOutputDriverNoStart(TestMatOutputParam,
                                 parent.TestFileOutputDriverNoStart):
    r"""Test runner for MatOutputDriver."""
    pass


class TestMatOutputDriver(TestMatOutputParam, parent.TestFileOutputDriver):
    r"""Test runner for MatOutputDriver."""
    pass
