import numpy as np
import nose.tools as nt
from cis_interface import backwards
from cis_interface.metaschema import datatypes
from cis_interface.metaschema.datatypes.ScalarMetaschemaType import (
    ScalarMetaschemaType)


def test_func():  # pragma: debug
    pass


_valid_objects = {'unicode': backwards.bytes2unicode('hello'),
                  'bytes': backwards.unicode2bytes('hello'),
                  'float': float(1), 'int': int(1),
                  'uint': np.uint(1), 'complex': complex(1, 1),
                  'object': {'a': 'hello'}, 'array': ['hello', 1],
                  'ply': {'vertices': [{k: 0.0 for k in 'xyz'},
                                       {k: 0.0 for k in 'xyz'},
                                       {k: 0.0 for k in 'xyz'}],
                          'faces': [{'vertex_index': [0, 1, 2]}]},
                  'obj': {'vertices': [{k: 0.0 for k in 'xyz'},
                                       {k: 0.0 for k in 'xyz'},
                                       {k: 0.0 for k in 'xyz'}],
                          'faces': [[{'vertex_index': 0},
                                     {'vertex_index': 1},
                                     {'vertex_index': 2}]]},
                  'schema': {'type': 'string'},
                  'function': test_func}


def test_get_type_class():
    r"""Test get_type_class."""
    for v in _valid_objects.keys():
        datatypes.get_type_class(v)
    nt.assert_raises(ValueError, datatypes.get_type_class, 'invalid')


def test_register_type_errors():
    r"""Test errors in register_type for duplicate."""
    nt.assert_raises(ValueError, datatypes.register_type, ScalarMetaschemaType)
    fake_prop = type('FakeType', (ScalarMetaschemaType, ),
                     {'name': 'number'})
    nt.assert_raises(ValueError, datatypes.register_type, fake_prop)
    fake_prop = type('FakeType', (ScalarMetaschemaType, ),
                     {'name': 'new', 'properties': ['invalid']})
    nt.assert_raises(ValueError, datatypes.register_type, fake_prop)


def test_add_type_from_schema_errors():
    r"""Test errors in add_type_from_schema."""
    nt.assert_raises(ValueError, datatypes.add_type_from_schema, 'invalid_file')


def test_get_type_from_def():
    r"""Test get_type_from_def."""
    datatypes.get_type_from_def('float')
    datatypes.get_type_from_def({'type': 'float'})
    datatypes.get_type_from_def({'a': 'float', 'b': 'int'})
    datatypes.get_type_from_def(['float', 'int'])
    nt.assert_raises(TypeError, datatypes.get_type_from_def, None)


def test_guess_type_from_msg():
    r"""Test guess_type_from_msg."""
    nt.assert_raises(ValueError, datatypes.guess_type_from_msg,
                     backwards.unicode2bytes('fake message'))


def test_guess_type_from_obj():
    r"""Test guess_type_from_obj."""
    invalid_objects = [object, object()]
    for t, x in _valid_objects.items():
        nt.assert_equal(datatypes.guess_type_from_obj(x).name, t)
    for x in invalid_objects:
        nt.assert_raises(datatypes.MetaschemaTypeError, datatypes.guess_type_from_obj, x)


def test_encode_decode():
    r"""Test encode/decode for valid objects."""
    for x in _valid_objects.values():
        y = datatypes.encode(x)
        z = datatypes.decode(y)
        nt.assert_equal(z, x)
        datatypes.encode_data(x)


def test_compare_schema():
    r"""Test for compare_schema."""
    valid = [
        ({'type': 'int'}, {'type': 'int'}),
        ({'type': 'int'}, {'type': 'scalar', 'subtype': 'int'}),
        ({'type': 'scalar', 'subtype': 'int'}, {'type': 'int'}),
        ({'type': 'int', 'unnamed': 0}, {'type': 'int', 'unnamed': 0})]
    invalid = [
        ({'type': 'int'}, {}), ({}, {'type': 'int'}),
        ({'type': 'int'}, {'type': 'int', 'precision': 4}),
        ({'type': 'int', 'unnamed': 0}, {'type': 'int', 'unnamed': 1})]
    for x in valid:
        errors = list(datatypes.compare_schema(*x))
        assert(not errors)
    for x in invalid:
        errors = list(datatypes.compare_schema(*x))
        assert(errors)
