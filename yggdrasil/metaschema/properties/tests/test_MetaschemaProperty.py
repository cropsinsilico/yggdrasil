from yggdrasil.tests import YggTestClassInfo, assert_equal
from yggdrasil.metaschema import get_validator, get_metaschema
from yggdrasil.metaschema.datatypes import MetaschemaTypeError
from yggdrasil.metaschema.properties.MetaschemaProperty import (
    create_property)


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
    assert_equal(new_prop.encode('hello'), None)
    assert_equal(list(new_prop.validate(None, None, None, None)), [])
    assert_equal(list(new_prop.compare(True, True)), [])
    assert_equal(list(new_prop.compare(True, False)), ['Test error'])


class TestMetaschemaProperty(YggTestClassInfo):
    r"""Test class for MetaschemaProperty class."""
    
    _mod = 'MetaschemaProperty'
    _cls = 'MetaschemaProperty'
    
    def __init__(self, *args, **kwargs):
        super(TestMetaschemaProperty, self).__init__(*args, **kwargs)
        self._valid = []
        self._invalid = []
        self._encode_errors = []
        self._valid_compare = [(0, 0)]
        self._invalid_compare = [(0, 1)]
        self._valid_normalize_schema = []
        self.validator = get_validator()(get_metaschema())

    @property
    def mod(self):
        r"""str: Absolute name of module containing class to be tested."""
        return 'yggdrasil.metaschema.properties.%s' % self._mod

    @property
    def inst_args(self):
        r"""dict: Keyword arguments for creating a class instance."""
        return tuple()

    def test_encode(self):
        r"""Test encode method for the class."""
        for (instance, value) in self._valid:
            x = self.import_cls.encode(instance)
            errors = list(self.import_cls.compare(x, value))
            assert(not errors)
        if self.import_cls.name == 'base':
            self.assert_raises(NotImplementedError, self.import_cls.encode, None)

    def test_encode_errors(self):
        r"""Test errors raised by encode."""
        for instance in self._encode_errors:
            self.assert_raises(MetaschemaTypeError, self.import_cls.encode, instance)

    def test_validate_valid(self):
        r"""Test validation method for the class on valid objects."""
        validator = self.validator
        for (instance, value) in self._valid:
            schema = {self.import_cls.name: value}
            errors = list(
                self.import_cls.wrapped_validate(validator, value, instance, schema))
            assert(not errors)
        # Instances not of the associate type validate as true (skipped)
        if self.import_cls.name == 'base':
            errors = list(
                self.import_cls.wrapped_validate(validator, None, None, {}))
        assert(not errors)

    def test_validate_invalid(self):
        r"""Test validation method for the class on invalid objects."""
        validator = self.validator
        for (instance, value) in self._invalid:
            schema = {self.import_cls.name: value}
            errors = list(
                self.import_cls.wrapped_validate(validator, value, instance, schema))
            assert(errors)

    def test_compare_valid(self):
        r"""Test comparision method for the class on valid objects."""
        for x in self._valid_compare:
            errors = list(self.import_cls.compare(*x))
            assert(not errors)

    def test_compare_invalid(self):
        r"""Test comparision method for the class on invalid objects."""
        for x in self._invalid_compare:
            errors = list(self.import_cls.compare(*x))
            assert(errors)

    def test_normalize_in_schema(self):
        r"""Test normalization in schema."""
        for x, y in self._valid_normalize_schema:
            self.assert_equal(self.import_cls.normalize_in_schema(x), y)
