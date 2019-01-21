import unittest
from yggdrasil.tests import scripts, assert_raises
from yggdrasil.drivers import LPyModelDriver
import yggdrasil.drivers.tests.test_ModelDriver as parent


@unittest.skipIf(LPyModelDriver._lpy_installed, "LPy is installed")
def test_LPyModelDriver_nolpy():  # pragma: no lpy
    r"""Test LPyModelDriver error when LPy not installed."""
    assert_raises(RuntimeError, LPyModelDriver.LPyModelDriver,
                  'test', scripts['lpy'])


class TestLPyModelParam(parent.TestModelParam):
    r"""Test parameters for LPyModelDriver class."""

    driver = 'LPyModelDriver'
    
    def __init__(self, *args, **kwargs):
        super(TestLPyModelParam, self).__init__(*args, **kwargs)
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
