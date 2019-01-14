import os
import nose.tools as nt
import cis_interface.drivers.tests.test_FileInputDriver as parent


class TestMatInputParam(parent.TestFileInputParam):
    r"""Test runner for MatInputDriver."""

    icomm_name = 'MatFileComm'
        

class TestMatInputDriverNoStart(TestMatInputParam,
                                parent.TestFileInputDriverNoStart):
    r"""Test runner for MatInputDriver without start."""
    pass


class TestMatInputDriver(TestMatInputParam, parent.TestFileInputDriver):
    r"""Test runner for MatInputDriver."""
    pass
