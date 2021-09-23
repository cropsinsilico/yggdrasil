r"""Tests for drivers sub-package."""
from yggdrasil import drivers


def test_create_driver(scripts):
    r"""Test driver creation w/ and w/o args."""
    drivers.create_driver('Driver', 'test_io_driver')
    drivers.create_driver('ExecutableModelDriver', 'test_model_driver',
                          args=scripts['python'])


__all__ = []
