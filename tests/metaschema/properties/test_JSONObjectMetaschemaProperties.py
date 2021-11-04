import pytest
from tests.metaschema.properties.test_MetaschemaProperty import (
    TestMetaschemaProperty as base_class)


class TestPropertiesMetaschemaProperty(base_class):
    r"""Test class for PropertiesMetaschemaProperty class."""
    
    _mod = 'yggdrasil.metaschema.properties.JSONObjectMetaschemaProperties'
    _cls = 'PropertiesMetaschemaProperty'

    @pytest.fixture(scope="class")
    def ele(self):
        r"""Test element"""
        return 'abc'

    @pytest.fixture(scope="class")
    def valid_value(self, ele):
        r"""Valid test value."""
        return {x: int(i) for i, x in enumerate(ele)}

    @pytest.fixture(scope="class")
    def valid_base(self, ele):
        r"""Base class for valid arrays."""
        return {x: {'type': 'int'} for x in ele}

    @pytest.fixture(scope="class")
    def invalid_type(self, ele):
        r"""Invalid type."""
        return {x: {'type': 'float'} for x in ele}

    @pytest.fixture(scope="class")
    def invalid_keys(self, ele):
        r"""Invalid keys."""
        return {x: {'type': 'int'} for x in ele[:-1]}

    @pytest.fixture(scope="class")
    def valid(self, valid_value, valid_base):
        r"""Objects that are valid."""
        return [(valid_value, valid_base)]

    @pytest.fixture(scope="class")
    def invalid(self, ele, valid_base):
        r"""Objects that are invalid."""
        return [({x: float(i) for i, x in enumerate(ele)}, valid_base)]

    @pytest.fixture(scope="class")
    def valid_compare(self, valid_base, invalid_keys):
        r"""Objects that successfully compare."""
        return [(valid_base, valid_base),
                (valid_base, invalid_keys)]

    @pytest.fixture(scope="class")
    def invalid_compare(self, valid_base, invalid_type, invalid_keys):
        r"""Objects that do not successfully compare."""
        return [(invalid_type, valid_base),
                (invalid_keys, valid_base)]
