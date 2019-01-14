import os
import nose.tools as nt
import tempfile
import cis_interface.drivers.tests.test_FileOutputDriver as parent


class TestObjFileOutputParam(parent.TestFileOutputParam):
    r"""Test parameters for ObjFileOutputDriver."""

    ocomm_name = 'ObjFileComm'


class TestObjFileOutputDriverNoStart(TestObjFileOutputParam,
                                     parent.TestFileOutputDriverNoStart):
    r"""Test runner for ObjFileOutputDriver without start."""
    pass


class TestObjFileOutputDriver(TestObjFileOutputParam,
                              parent.TestFileOutputDriver):
    r"""Test runner for ObjFileOutputDriver."""
    pass
