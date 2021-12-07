import pytest
from yggdrasil.drivers.ODEModelDriver import ODEModel, ODEError


def test_derivative_regexs():
    r"""Test that regexes identify derivatives."""
    pairs = [
        ('dx/dt = x**2',
         [{'name': 'dx/dt', 't': 't', 'f': 'x', 'n': 1, 'tval': None}]),
        ('d^2x/dt^2 = 1 + t',
         [{'name': 'd^2x/dt^2', 't': 't', 'f': 'x', 'n': 2, 'tval': None}]),
        ('y\'\'(x) = x + 5',
         [{'name': 'y\'\'(x)', 't': 'x', 'f': 'y', 'n': 2, 'tval': 'x'}])]
    for x, y in pairs:
        assert(ODEModel.extract_derivatives(x) == y)


def test_mistmatched_t():
    r"""Test error handling when equations have conflicting time values."""
    with pytest.raises(ODEError):
        ODEModel(['dx/dt = x**2', 'dy/dq = y**2'])
    with pytest.raises(ODEError):
        ODEModel(['dx(0)/dt = 5.0'])
