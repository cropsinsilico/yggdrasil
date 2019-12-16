import numpy as np
from yggdrasil.tests import YggTestBase
from yggdrasil import units


class TestUnits(YggTestBase):
    r"""Tests for using pint for units."""

    def setup(self, *args, **kwargs):
        r"""Setup, create variables for testing."""
        self._vars_nounits = [1.0, np.zeros(5), int(1)]
        self._vars_units = [units.add_units(v, 'cm') for v in self._vars_nounits]
        super(TestUnits, self).setup(*args, **kwargs)

    def test_has_units(self):
        r"""Test has_units."""
        for v in self._vars_nounits:  # + ['string']:
            assert(not units.has_units(v))
        for v in self._vars_units:
            assert(units.has_units(v))

    def test_get_data(self):
        r"""Test get_data."""
        for v in self._vars_nounits:
            self.assert_equal(units.get_data(v), v)
        for vno, v in zip(self._vars_nounits, self._vars_units):
            self.assert_equal(units.get_data(v), np.array(vno))

    def test_get_units(self):
        r"""Test get_units."""
        for v in self._vars_nounits:
            self.assert_equal(units.get_units(v), '')
        for v in self._vars_units:
            self.assert_equal(units.get_units(v), str(units.as_unit('cm').units))

    def test_add_units(self):
        r"""Test add_units."""
        for v in self._vars_nounits:
            x = units.add_units(v, 'cm')
            assert(units.has_units(x))
        self.assert_equal(units.add_units(1.0, ''), 1.0)
        self.assert_equal(units.add_units(1.0, 'n/a'), 1.0)

    def test_is_null_unit(self):
        r"""Test is_null_unit."""
        assert(units.is_null_unit('n/a'))
        assert(units.is_null_unit(''))
        assert(not units.is_null_unit('cm'))

    def test_as_unit(self):
        r"""Test as_unit."""
        units.as_unit('cm')
        self.assert_raises(ValueError, units.as_unit, 'invalid')

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

    def test_convert_to(self):
        r"""Test convert_to."""
        units.convert_to(1, 'm')
        for v in self._vars_units:
            units.convert_to(v, 'm')
            self.assert_raises(ValueError, units.convert_to, v, 's')

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
                 ('g2 km s-2', '(g**2)*km*(s**-2)')]
        for x, y in pairs:
            self.assert_equal(units.convert_R_unit_string(x), y)
