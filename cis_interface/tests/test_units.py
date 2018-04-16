from cis_interface import units


def test_is_unit():
    r"""Test is_unit."""
    assert(units.is_unit('n/a'))
    assert(units.is_unit(''))
    assert(units.is_unit('cm/s**2'))
    assert(units.is_unit('cm/s^2'))
    assert(units.is_unit('umol'))
    assert(units.is_unit('mmol'))
    assert(not units.is_unit('invalid'))
