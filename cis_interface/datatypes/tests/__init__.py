import numpy as np
import nose.tools as nt
from cis_interface import datatypes, backwards
from cis_interface.datatypes.CisArrayType import CisScalarType


def test_get_type_class():
    r"""Test get_type_class."""
    valid_types = ['scalar', '1darray', 'ndarray']
    for v in valid_types:
        datatypes.get_type_class(v)
    nt.assert_raises(ValueError, datatypes.get_type_class, 'invalid')


def test_error_duplicate():
    r"""Test error in register_type for duplicate."""
    nt.assert_raises(ValueError, datatypes.register_type, CisScalarType)


def test_guess_type_from_msg():
    r"""Test guess_type_from_msg."""
    nt.assert_raises(ValueError, datatypes.guess_type_from_msg,
                     backwards.unicode2bytes('fake message'))


def test_guess_type_from_obj():
    r"""Test guess_type_from_obj."""
    valid_objects = [backwards.bytes2unicode('hello'),
                     backwards.unicode2bytes('hello'),
                     float(1), int(1), np.uint(1), complex(1, 1)]
    invalid_objects = [{'a': 'hello'}, ['hello', 1], CisScalarType]
    for x in valid_objects:
        datatypes.guess_type_from_obj(x)
    for x in invalid_objects:
        nt.assert_raises(ValueError, datatypes.guess_type_from_obj, x)
