import pytest
from yggdrasil.metaschema import (
    get_validator, get_metaschema, MetaschemaTypeError)
from yggdrasil.metaschema.properties.MetaschemaProperty import (
    create_property)
from tests import TestClassBase as base_class


def test_dynamic():
    r"""Test dynamic creation of property."""

    def encode(instance, typedef=None):
        return None

    def validate(validator, value, instance, schema):
        return

    def compare(prop1, prop2):
        if not prop2:
            yield 'Test error'
        return

    new_prop = create_property('invalid', None, encode, validate, compare,
                               dont_register=True)
    assert(new_prop.encode('hello') is None)
    assert(list(new_prop.validate(None, None, None, None)) == [])
    assert(list(new_prop.compare(True, True)) == [])
    assert(list(new_prop.compare(True, False)) == ['Test error'])


class TestMetaschemaProperty(base_class):
    r"""Test class for MetaschemaProperty class."""
    
    _mod = 'yggdrasil.metaschema.properties.MetaschemaProperty'
    _cls = 'MetaschemaProperty'

    @pytest.fixture(scope="class")
    def valid(self):
        r"""Objects that are valid."""
        return []

    @pytest.fixture(scope="class")
    def invalid(self):
        r"""Objects that are invalid."""
        return []

    @pytest.fixture(scope="class")
    def encode_errors(self):
        r"""Object that enduce errors during encoding."""
        return []

    @pytest.fixture(scope="class")
    def valid_compare(self):
        r"""Objects that successfully compare."""
        return [(0, 0)]

    @pytest.fixture(scope="class")
    def invalid_compare(self):
        r"""Objects that do not successfully compare."""
        return [(0, 1)]

    @pytest.fixture(scope="class")
    def valid_normalize_schema(self):
        r"""Schemas for normalization."""
        return []

    @pytest.fixture(scope="class")
    def validator(self):
        r"""Schema validator."""
        return get_validator()(get_metaschema())
    
    def test_encode(self, python_class, valid):
        r"""Test encode method for the class."""
        for (instance, value) in valid:
            x = python_class.encode(instance)
            errors = list(python_class.compare(x, value))
            assert(not errors)
        if python_class.name == 'base':
            with pytest.raises(NotImplementedError):
                python_class.encode(None)

    def test_encode_errors(self, python_class, encode_errors):
        r"""Test errors raised by encode."""
        for instance in encode_errors:
            with pytest.raises(MetaschemaTypeError):
                python_class.encode(instance)

    def test_validate_valid(self, python_class, validator, valid):
        r"""Test validation method for the class on valid objects."""
        for (instance, value) in valid:
            schema = {python_class.name: value}
            errors = list(
                python_class.wrapped_validate(validator, value, instance, schema))
            assert(not errors)
        # Instances not of the associate type validate as true (skipped)
        if python_class.name == 'base':
            errors = list(
                python_class.wrapped_validate(validator, None, None, {}))
        assert(not errors)

    def test_validate_invalid(self, python_class, validator, invalid):
        r"""Test validation method for the class on invalid objects."""
        for (instance, value) in invalid:
            schema = {python_class.name: value}
            errors = list(
                python_class.wrapped_validate(validator, value, instance, schema))
            assert(errors)

    def test_compare_valid(self, python_class, valid_compare):
        r"""Test comparision method for the class on valid objects."""
        for x in valid_compare:
            errors = list(python_class.compare(*x))
            assert(not errors)

    def test_compare_invalid(self, python_class, invalid_compare):
        r"""Test comparision method for the class on invalid objects."""
        for x in invalid_compare:
            errors = list(python_class.compare(*x))
            assert(errors)

    def test_normalize_in_schema(self, python_class, valid_normalize_schema):
        r"""Test normalization in schema."""
        for x, y in valid_normalize_schema:
            assert(python_class.normalize_in_schema(x) == y)
