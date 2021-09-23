import pytest
from tests.metaschema.properties.test_ArgsMetaschemaProperty import (
    TestArgsMetaschemaProperty as base_class)


class TestKwargsMetaschemaProperty(base_class):
    r"""Test class for KwargsMetaschemaProperty class."""
    
    _mod = 'yggdrasil.metaschema.properties.KwargsMetaschemaProperty'
    _cls = 'KwargsMetaschemaProperty'
    
    @pytest.fixture(scope="class")
    def valid(self, valid_instances):
        r"""Objects that are valid."""
        return [(x, x.__class__.valid_kwargs) for x in valid_instances]

    @pytest.fixture(scope="class")
    def invalid(self, valid_instances):
        r"""Objects that are invalid."""
        return [(x, x.__class__.invalid_kwargs) for x in valid_instances]

    @pytest.fixture(scope="class")
    def valid_type(self, valid_classes):
        r"""Valid type."""
        return valid_classes[0].valid_kwargs
    
    @pytest.fixture(scope="class")
    def invalid_type(self, valid_classes):
        r"""Invalid type."""
        return valid_classes[0].invalid_kwargs
