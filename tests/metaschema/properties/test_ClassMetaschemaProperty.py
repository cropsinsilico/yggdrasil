import pytest
from tests.metaschema.properties.test_MetaschemaProperty import (
    TestMetaschemaProperty as base_class)


class TestClassMetaschemaProperty(base_class):
    r"""Test class for ClassMetaschemaProperty class."""
    
    _mod = 'yggdrasil.metaschema.properties.ClassMetaschemaProperty'
    _cls = 'ClassMetaschemaProperty'
    
    @pytest.fixture(scope="class")
    def valid(self):
        r"""Objects that are valid."""
        return [(int(1), int), (dict(), dict)]

    @pytest.fixture(scope="class")
    def invalid(self):
        r"""Objects that are invalid."""
        return [(int(1), dict), (dict(), int)]

    @pytest.fixture(scope="class")
    def valid_compare(self):
        r"""Objects that successfully compare."""
        return [(int, int), (int, (int, float)),
                ([int, float], int),
                ([int, float], (dict, float))]

    @pytest.fixture(scope="class")
    def invalid_compare(self):
        r"""Objects that do not successfully compare."""
        return [(int, float), (int, (dict, float)),
                ((int, dict), float),
                ((int, float), (dict, list))]
