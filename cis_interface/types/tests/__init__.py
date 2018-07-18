import nose.tools as nt
from cis_interface import types
from cis_interface.types.CisArrayType import CisScalarType


def test_get_type_class():
    r"""Test get_type_class."""
    valid_types = ['scalar', '1darray', 'ndarray']
    for v in valid_types:
        types.get_type_class(v)
    nt.assert_raises(ValueError, types.get_type_class, 'invalid')


def test_error_duplicate():
    r"""Test error in register_type for duplicate."""
    nt.assert_raises(ValueError, types.register_type, CisScalarType)
