import numpy as np
import cis_interface.drivers.tests.test_FileOutputDriver as parent


class TestPandasFileOutputParam(parent.TestFileOutputParam):
    r"""Test parameters for PandasFileOutputDriver."""

    ocomm_name = 'PandasFileComm'


class TestPandasFileOutputDriverNoStart(TestPandasFileOutputParam,
                                        parent.TestFileOutputDriverNoStart):
    r"""Test runner for PandasFileOutputDriver without start."""
    pass


class TestPandasFileOutputDriver(TestPandasFileOutputParam,
                                 parent.TestFileOutputDriver):
    r"""Test runner for PandasFileOutputDriver."""
    pass
