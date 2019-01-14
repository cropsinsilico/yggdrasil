import os
import tempfile
import nose.tools as nt
import cis_interface.drivers.tests.test_FileInputDriver as parent


class TestPickleFileInputParam(parent.TestFileInputParam):
    r"""Test parameters for PickleFileInputDriver."""

    icomm_name = 'PickleFileComm'


class TestPickleFileInputDriverNoStart(TestPickleFileInputParam,
                                       parent.TestFileInputDriverNoStart):
    r"""Test runner for PickleFileInputDriver without start."""
    pass


class TestPickleFileInputDriver(TestPickleFileInputParam,
                                parent.TestFileInputDriver):
    r"""Test runner for PickleFileInputDriver."""
    pass
