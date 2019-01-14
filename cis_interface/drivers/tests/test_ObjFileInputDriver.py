import os
import tempfile
import nose.tools as nt
import cis_interface.drivers.tests.test_FileInputDriver as parent


class TestObjFileInputParam(parent.TestFileInputParam):
    r"""Test parameters for ObjFileInputDriver."""

    icomm_name = 'ObjFileComm'


class TestObjFileInputDriverNoStart(TestObjFileInputParam,
                                    parent.TestFileInputDriverNoStart):
    r"""Test runner for ObjFileInputDriver without start."""
    pass


class TestObjFileInputDriver(TestObjFileInputParam,
                             parent.TestFileInputDriver):
    r"""Test runner for ObjFileInputDriver."""
    pass
