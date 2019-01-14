import numpy as np
import nose.tools as nt
from cis_interface import serialize
import cis_interface.drivers.tests.test_FileInputDriver as parent


class TestPandasFileInputParam(parent.TestFileInputParam):
    r"""Test parameters for PandasFileInputDriver."""

    icomm_name = 'PandasFileComm'

        
class TestPandasFileInputDriverNoStart(TestPandasFileInputParam,
                                       parent.TestFileInputDriverNoStart):
    r"""Test runner for PandasFileInputDriver."""
    pass


class TestPandasFileInputDriver(TestPandasFileInputParam,
                                parent.TestFileInputDriver):
    r"""Test runner for PandasFileInputDriver."""
    pass
