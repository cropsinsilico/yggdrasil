import os
import tempfile
import cis_interface.drivers.tests.test_FileOutputDriver as parent


class TestPickleFileOutputParam(parent.TestFileOutputParam):
    r"""Test parameters for PickleFileOutputDriver."""

    ocomm_name = 'PickleFileComm'


class TestPickleFileOutputDriverNoStart(TestPickleFileOutputParam,
                                        parent.TestFileOutputDriverNoStart):
    r"""Test runner for PickleFileOutputDriver without start."""
    pass


class TestPickleFileOutputDriver(TestPickleFileOutputParam,
                                 parent.TestFileOutputDriver):
    r"""Test runner for PickleFileOutputDriver."""
    pass
