import os
import nose.tools as nt
import tempfile
import cis_interface.drivers.tests.test_FileOutputDriver as parent


class TestPlyFileOutputParam(parent.TestFileOutputParam):
    r"""Test parameters for PlyFileOutputDriver."""

    ocomm_name = 'PlyFileComm'


class TestPlyFileOutputDriverNoStart(TestPlyFileOutputParam,
                                     parent.TestFileOutputDriverNoStart):
    r"""Test runner for PlyFileOutputDriver without start."""
    pass


class TestPlyFileOutputDriver(TestPlyFileOutputParam,
                              parent.TestFileOutputDriver):
    r"""Test runner for PlyFileOutputDriver."""
    pass
