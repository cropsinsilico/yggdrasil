r"""Tests for drivers sub-package."""
from yggdrasil import drivers
from yggdrasil.drivers import Driver, ModelDriver, ConnectionDriver
from yggdrasil.tests import scripts, assert_equal


def test_import_driver():
    r"""Check a few drivers."""
    drvs = [('Driver', Driver.Driver),
            ('ModelDriver', ModelDriver.ModelDriver),
            ('ConnectionDriver', ConnectionDriver.ConnectionDriver)]
    for n, dans in drvs:
        dres = drivers.import_driver(n)
        assert_equal(dres, dans)


def test_create_driver():
    r"""Test driver creation w/ and w/o args."""
    drivers.create_driver('Driver', 'test_io_driver')
    drivers.create_driver('ModelDriver', 'test_model_driver',
                          args=scripts['python'])


__all__ = []
