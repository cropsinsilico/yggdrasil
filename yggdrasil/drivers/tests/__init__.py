r"""Tests for drivers sub-package."""
from yggdrasil import drivers
from yggdrasil.tests import scripts


def test_create_driver():
    r"""Test driver creation w/ and w/o args."""
    drivers.create_driver('Driver', 'test_io_driver')
    drivers.create_driver('ExecutableModelDriver', 'test_model_driver',
                          args=scripts['python'])


__all__ = []
