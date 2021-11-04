import pytest
import numpy as np
from tests import TestBase as base_class
from yggdrasil import units, tools


class DummyUnits(int):
    r"""Dummy class for testing that has units attribute."""

    units = 'cm'


class TestUnits(base_class):
    r"""Tests for using pint for units."""

    @pytest.fixture(scope="class")
    def vars_nounits(self):
        return [1.0, np.zeros(5), int(1), DummyUnits(1)]

    @pytest.fixture(scope="class")
    def vars_units(self, vars_nounits):
        return [units.add_units(v, 'cm') for v in vars_nounits
                if not isinstance(v, DummyUnits)]

    def test_has_units(self, vars_nounits, vars_units):
        r"""Test has_units."""
        for v in vars_nounits:
            assert(not units.has_units(v))
        for v in vars_units:
            assert(units.has_units(v))

    def test_invalid_unit(self):
        r"""Test error when an invalid unit is added."""
        with pytest.raises(ValueError):
            units.add_units(1.0, 'invalid')

    def test_get_data(self, vars_units, vars_nounits, nested_approx):
        r"""Test get_data."""
        for v in vars_nounits:
            assert(units.get_data(v) == nested_approx(v))
        for vno, v in zip(vars_nounits, vars_units):
            assert(units.get_data(v) == nested_approx(vno))

    def test_get_units(self, vars_units, vars_nounits):
        r"""Test get_units."""
        for v in vars_nounits:
            assert(units.get_units(v) == '')
        for v in vars_units:
            assert(units.get_units(v) == str(units.as_unit('cm').units))

    def test_add_units(self, vars_nounits):
        r"""Test add_units."""
        for v in vars_nounits:
            x = units.add_units(v, 'cm')
            assert(units.has_units(x))
        assert(units.add_units(1.0, '') == 1.0)
        assert(units.add_units(1.0, 'n/a') == 1.0)

    def test_is_null_unit(self):
        r"""Test is_null_unit."""
        assert(units.is_null_unit('n/a'))
        assert(units.is_null_unit(''))
        assert(not units.is_null_unit('cm'))

    def test_as_unit(self):
        r"""Test as_unit."""
        units.as_unit('cm')
        with pytest.raises(ValueError):
            units.as_unit('invalid')

    def test_is_unit(self):
        r"""Test is_unit."""
        assert(units.is_unit('n/a'))
        assert(units.is_unit(''))
        assert(units.is_unit('cm/s**2'))
        # Not supported by unyt
        # assert(units.is_unit('cm/s^2'))
        assert(units.is_unit('umol'))
        assert(units.is_unit('mmol'))
        assert(not units.is_unit('invalid'))

    def test_convert_to(self, vars_units):
        r"""Test convert_to."""
        units.convert_to(1, 'm')
        for v in vars_units:
            units.convert_to(v, 'm')
            with pytest.raises(ValueError):
                units.convert_to(v, 's')
        x = units.add_units(int(1), 'umol')
        units.convert_to(x, 'mol')

    def test_are_compatible(self):
        r"""Test are_compatible."""
        assert(units.are_compatible('cm', 'm'))
        assert(units.are_compatible('cm', ''))
        assert(not units.are_compatible('cm', 's'))
        assert(not units.are_compatible('cm', 'invalid'))
        assert(units.are_compatible('d', 'hr'))
        assert(units.are_compatible('hr', 'd'))

    def test_convert_R_unit_string(self):
        r"""Test convert_R_unit_string."""
        pairs = [('g', 'g'), ('g2', '(g**2)'),
                 ('g2 km s-2', '(g**2)*km*(s**-2)'),
                 ('degC d', 'degC*d'),
                 (tools.bytes2str(b'\xc2\xb0C d'),
                  tools.bytes2str(b'\xc2\xb0C*d')),
                 ('h', 'hr'),
                 ('hrs/kg', 'hr/kg'),
                 ('', ''),
                 ('cm**(-2)', '(cm**-2)')]
        for x, y in pairs:
            assert(units.convert_R_unit_string(x) == y)
            assert(units.convert_R_unit_string(y) == y)
            units.add_units(1.0, x)
