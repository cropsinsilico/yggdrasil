import os
import tempfile
import nose.tools as nt
import cis_interface.drivers.tests.test_FileInputDriver as parent


class TestAsciiMapInputParam(parent.TestFileInputParam):
    r"""Test parameters for AsciiMapInputDriver."""

    icomm_name = 'AsciiMapComm'


class TestAsciiMapInputDriverNoStart(TestAsciiMapInputParam,
                                     parent.TestFileInputDriverNoStart):
    r"""Test runner for AsciiMapInputDriver without start."""
    pass


class TestAsciiMapInputDriver(TestAsciiMapInputParam,
                              parent.TestFileInputDriver):
    r"""Test runner for AsciiMapInputDriver."""
    pass
