r"""Tests for drivers sub-package."""
import nose.tools as nt
from cis_interface import drivers
from cis_interface.drivers import Driver, ModelDriver, IODriver
from cis_interface.tests import scripts


def test_import_driver():
    r"""Check a few drivers."""
    drvs = [('Driver', Driver.Driver),
            ('ModelDriver', ModelDriver.ModelDriver),
            ('IODriver', IODriver.IODriver)]
    for n, dans in drvs:
        dres = drivers.import_driver(n)
        nt.assert_equal(dres, dans)


def test_create_driver():
    r"""Test driver creation w/ and w/o args."""
    drivers.create_driver('Driver', 'test_io_driver')
    drivers.create_driver('ModelDriver', 'test_model_driver',
                          args=scripts['python'])


__all__ = []
