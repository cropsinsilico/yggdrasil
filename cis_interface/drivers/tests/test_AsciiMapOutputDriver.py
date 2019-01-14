import os
import tempfile
from cis_interface import backwards
import cis_interface.drivers.tests.test_FileOutputDriver as parent


class TestAsciiMapOutputParam(parent.TestFileOutputParam):
    r"""Test parameters for AsciiMapOutputDriver."""

    ocomm_name = 'AsciiMapComm'


class TestAsciiMapOutputDriverNoStart(TestAsciiMapOutputParam,
                                      parent.TestFileOutputDriverNoStart):
    r"""Test runner for AsciiMapOutputDriver without start."""
    pass


class TestAsciiMapOutputDriver(TestAsciiMapOutputParam,
                               parent.TestFileOutputDriver):
    r"""Test runner for AsciiMapOutputDriver."""
    pass
