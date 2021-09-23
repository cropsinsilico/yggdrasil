import pytest
from tests.metaschema.properties.test_MetaschemaProperty import (
    TestMetaschemaProperty as base_class)


class TestTemptypeMetaschemaProperty(base_class):
    r"""Test class for TemptypeMetaschemaProperty class."""
    
    _mod = 'yggdrasil.metaschema.properties.AnyMetaschemaProperties'
    _cls = 'TemptypeMetaschemaProperty'
    
    @pytest.fixture(scope="class")
    def valid(self):
        r"""Objects that are valid."""
        return [(int(1), {'type': 'int'}),
                ([int(1), float(1)],
                 {'type': 'array',
                  'items': [{'type': 'int'}, {'type': 'float'}]}),
                ({'a': int(1), 'b': float(2)},
                 {'type': 'object',
                  'properties': {
                      'a': {'type': 'int'},
                      'b': {'type': 'float'}}})]

    @pytest.fixture(scope="class")
    def invalid(self):
        r"""Objects that are invalid."""
        return [(int(1), {'type': 'float'})]

    @pytest.fixture(scope="class")
    def valid_compare(self):
        r"""Objects that successfully compare."""
        return [({'type': 'int'}, {'type': 'int'})]

    @pytest.fixture(scope="class")
    def invalid_compare(self):
        r"""Objects that do not successfully compare."""
        return [({'type': 'int'}, {'type': 'float'})]
