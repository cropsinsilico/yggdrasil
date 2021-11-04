import pytest
from tests.metaschema.datatypes.test_JSONObjectMetaschemaType import (
    TestJSONObjectMetaschemaType as base_class)
import copy
# from yggdrasil.metaschema.datatypes import compare_schema


class TestSchemaMetaschemaType(base_class):
    r"""Test class for SchemaMetaschemaType class."""

    _mod = 'yggdrasil.metaschema.datatypes.SchemaMetaschemaType'
    _cls = 'SchemaMetaschemaType'

    @pytest.fixture(scope="class")
    def value(self, fulldef):
        r"""dict: Test value."""
        return dict(copy.deepcopy(fulldef), type='object')
    
    @pytest.fixture(scope="class")
    def fulldef(self):
        r"""dict: Full type definitions."""
        return {'type': 'schema'}

    @pytest.fixture(scope="class")
    def typedef_base(self):
        r"""dict: Base type definition."""
        return {'type': 'schema'}
    
    @pytest.fixture(scope="class")
    def valid_encoded(self, fulldef):
        r"""list: Encoded objects that are valid under this type."""
        return [fulldef]
    
    @pytest.fixture(scope="class")
    def valid_decoded(self, value):
        r"""list: Objects that are valid under this type."""
        return [value]
    
    @pytest.fixture(scope="class")
    def invalid_encoded(self):
        r"""list: Encoded objects that are invalid under this type."""
        return [{}]

    @pytest.fixture(scope="class")
    def invalid_decoded(self):
        r"""list: Objects that are invalid under this type."""
        return [{}]
        
    @pytest.fixture(scope="class")
    def compatible_objects(self, value):
        r"""list: Objects that are compatible with this type."""
        return [(value, value, None)]

    @pytest.fixture(scope="class")
    def valid_normalize(self):
        r"""list: Pairs of pre-/post-normalized objects."""
        return [('float', {'type': 'float',
                           'precision': 64}),
                ({'units': 'g'}, {'units': 'g',
                                  'type': 'scalar',
                                  'subtype': 'float',
                                  'precision': 64}),
                ({'title': 'a'}, {'title': 'a'}),
                ({'title': 'a', 'units': 'g'},
                 {'title': 'a', 'units': 'g',
                  'type': 'scalar', 'subtype': 'float',
                  'precision': 64}),
                ({}, {})]

    # @classmethod
    # def assert_result_equal(cls, x, y):
    #     r"""Assert that serialized/deserialized objects equal."""
    #     compare_schema(x, y)
