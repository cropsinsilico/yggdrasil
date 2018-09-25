import nose.tools as nt
import unittest
from cis_interface.tests import scripts
from cis_interface.drivers import LPyModelDriver
import cis_interface.drivers.tests.test_ModelDriver as parent


@unittest.skipIf(LPyModelDriver._lpy_installed, "LPy is installed")
def test_LPyModelDriver_nolpy():  # pragma: no lpy
    r"""Test LPyModelDriver error when LPy not installed."""
    nt.assert_raises(RuntimeError, LPyModelDriver.LPyModelDriver,
                     'test', scripts['lpy'])


class TestLPyModelParam(parent.TestModelParam):
    r"""Test parameters for LPyModelDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestLPyModelParam, self).__init__(*args, **kwargs)
        self.driver = 'LPyModelDriver'
        self.args = [scripts['lpy']]

        
@unittest.skipIf(not LPyModelDriver._lpy_installed, "LPy is not installed")
class TestLPyModelDriverNoStart(TestLPyModelParam,
                                parent.TestModelDriverNoStart):  # pragma: lpy
    r"""Test runner for LPyModelDriver class without starting the driver."""
    pass


@unittest.skipIf(not LPyModelDriver._lpy_installed, "LPy is not installed")
class TestLPyModelDriver(TestLPyModelParam,
                         parent.TestModelDriver):  # pragma: lpy
    r"""Test runner for LPyModelDriver class."""
    pass
