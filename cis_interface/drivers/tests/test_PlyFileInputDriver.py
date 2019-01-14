import os
import tempfile
import nose.tools as nt
import cis_interface.drivers.tests.test_FileInputDriver as parent


class TestPlyFileInputParam(parent.TestFileInputParam):
    r"""Test parameters for PlyFileInputDriver."""

    icomm_name = 'PlyFileComm'


class TestPlyFileInputDriverNoStart(TestPlyFileInputParam,
                                    parent.TestFileInputDriverNoStart):
    r"""Test runner for PlyFileInputDriver without start."""
    pass


class TestPlyFileInputDriver(TestPlyFileInputParam,
                             parent.TestFileInputDriver):
    r"""Test runner for PlyFileInputDriver."""
    pass
