import pytest
from yggdrasil.metaschema import datatypes, MetaschemaTypeError
from yggdrasil.metaschema.datatypes.ScalarMetaschemaType import (
    ScalarMetaschemaType)
from tests.metaschema import _valid_objects


def test_registry_operations():
    r"""Test access to registry dictionary operations."""
    datatypes._type_registry.items()
    datatypes._type_registry.keys()
    datatypes._type_registry.values()


def test_get_type_class():
    r"""Test get_type_class."""
    for v in _valid_objects.keys():
        datatypes.get_type_class(v)
    with pytest.raises(ValueError):
        datatypes.get_type_class('invalid')


def test_register_type_errors():
    r"""Test errors in register_type for duplicate."""
    with pytest.raises(ValueError):
        datatypes.register_type(ScalarMetaschemaType)
    type_args = ('FakeType', (ScalarMetaschemaType, ),
                 {'name': 'new', 'properties': ['invalid']})
    with pytest.raises(ValueError):
        type(*type_args)
    

def test_add_type_from_schema_errors():
    r"""Test errors in add_type_from_schema."""
    with pytest.raises(ValueError):
        datatypes.add_type_from_schema('invalid_file')


def test_get_type_from_def():
    r"""Test get_type_from_def."""
    datatypes.get_type_from_def('float')
    datatypes.get_type_from_def({'type': 'float'})
    datatypes.get_type_from_def({'a': 'float', 'b': 'int'})
    datatypes.get_type_from_def(['float', 'int'])
    with pytest.raises(TypeError):
        datatypes.get_type_from_def(None)


def test_guess_type_from_msg():
    r"""Test guess_type_from_msg."""
    with pytest.raises(ValueError):
        datatypes.guess_type_from_msg(b'fake message')


def test_guess_type_from_obj():
    r"""Test guess_type_from_obj."""
    invalid_objects = [object()]  # , object()]
    for t, x in _valid_objects.items():
        assert(datatypes.guess_type_from_obj(x).name == t)
    for x in invalid_objects:
        with pytest.raises(MetaschemaTypeError):
            datatypes.guess_type_from_obj(x)


def test_encode_decode(nested_approx):
    r"""Test encode/decode for valid objects."""
    for x in _valid_objects.values():
        y = datatypes.encode(x)
        z = datatypes.decode(y)
        assert(z == nested_approx(x))
        t = datatypes.encode_type(x)
        d = datatypes.encode_data(x)
        w = datatypes.decode_data(d, t)
        assert(w == nested_approx(x))
    with pytest.raises(ValueError):
        datatypes.decode_data(b'', None)


def test_encode_decode_readable():
    r"""Test encode_data_reable/decode for valid objects."""
    for x in _valid_objects.values():
        datatypes.encode_data_readable(x)
        

def test_compare_schema():
    r"""Test for compare_schema."""
    valid = [
        ({'type': 'int'}, {'type': 'int'}),
        ({'type': 'int'}, {'type': 'scalar', 'subtype': 'int'}),
        ({'type': 'scalar', 'subtype': 'int'}, {'type': 'int'}),
        ({'type': 'int', 'unnamed': 0}, {'type': 'int', 'unnamed': 1}),
        ({'type': 'int', 'unnamed': 0}, {'type': 'int'}),
        ({'type': 'object', 'definitions': {'a': {'type': 'int'}},
          'properties': {'x': {'$ref': '#/definitions/a'}}},
         {'type': 'object', 'definitions': {'b': {'type': 'int'}},
          'properties': {'x': {'$ref': '#/definitions/b'}}}),
        ({'type': 'object', 'properties': {'x': {'type': 'float'}}},
         {'type': 'object', 'properties': {'x': {'type': 'float'},
                                           'y': {'type': 'float'}},
          'required': ['x']})]
    invalid = [
        ({'type': 'int'}, {}), ({}, {'type': 'int'}),
        ({'type': 'int'}, {'type': 'int', 'precision': 4}),
        ({'type': 'object', 'definitions': {'a': {'type': 'float'}},
          'properties': {'x': {'$ref': '#/definitions/a'}}},
         {'type': 'object', 'definitions': {'b': {'type': 'int'}},
          'properties': {'x': {'$ref': '#/definitions/b'}}})]
    for x in valid:
        errors = list(datatypes.compare_schema(*x))
        assert(not errors)
    for x in invalid:
        errors = list(datatypes.compare_schema(*x))
        assert(errors)
