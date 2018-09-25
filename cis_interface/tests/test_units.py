import nose.tools as nt
import numpy as np
from cis_interface.tests import CisTestBase
from cis_interface import units


class TestPint(CisTestBase):
    r"""Tests for using pint for units."""
    _unit_package = 'pint'

    def setup(self, *args, **kwargs):
        r"""Set use_unyt for tests."""
        self._old_use_unyt = units._use_unyt
        if self._unit_package == 'unyt':
            units._use_unyt = True
        else:
            units._use_unyt = False
        self._vars_nounits = [1.0, np.zeros(5), int(1)]
        self._vars_units = [units.add_units(v, 'cm') for v in self._vars_nounits]
        super(TestPint, self).setup(*args, **kwargs)

    def teardown(self, *args, **kwargs):
        r"""Reset use_unyt to default."""
        units._use_unyt = self._old_use_unyt
        super(TestPint, self).teardown(*args, **kwargs)

    def test_has_units(self):
        r"""Test has_units."""
        for v in self._vars_nounits:  # + ['string']:
            assert(not units.has_units(v))
        for v in self._vars_units:
            assert(units.has_units(v))

    def test_get_data(self):
        r"""Test get_data."""
        for v in self._vars_nounits:
            np.testing.assert_array_equal(units.get_data(v), v)
        for vno, v in zip(self._vars_nounits, self._vars_units):
            np.testing.assert_array_equal(units.get_data(v), np.array(vno))

    def test_get_units(self):
        r"""Test get_units."""
        for v in self._vars_nounits:
            nt.assert_equal(units.get_units(v), '')
        for v in self._vars_units:
            nt.assert_equal(units.get_units(v), str(units.as_unit('cm').units))

    def test_add_units(self):
        r"""Test add_units."""
        for v in self._vars_nounits:
            x = units.add_units(v, 'cm')
            assert(units.has_units(x))
        nt.assert_equal(units.add_units(1.0, ''), 1.0)
        nt.assert_equal(units.add_units(1.0, 'n/a'), 1.0)

    def test_is_null_unit(self):
        r"""Test is_null_unit."""
        assert(units.is_null_unit('n/a'))
        assert(units.is_null_unit(''))
        assert(not units.is_null_unit('cm'))

    def test_as_unit(self):
        r"""Test as_unit."""
        units.as_unit('cm')
        nt.assert_raises(ValueError, units.as_unit, 'invalid')

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
            nt.assert_raises(ValueError, units.convert_to, v, 's')

    def test_are_compatible(self):
        r"""Test are_compatible."""
        assert(units.are_compatible('cm', 'm'))
        assert(units.are_compatible('cm', ''))
        assert(not units.are_compatible('cm', 's'))
        assert(not units.are_compatible('cm', 'invalid'))


class TestUnyt(TestPint):
    r"""Test for using unyt for units."""
    _unit_package = 'unyt'
