import pytest
from tests.metaschema.properties.test_MetaschemaProperty import (
    TestMetaschemaProperty as base_class)


class TestItemsMetaschemaProperty(base_class):
    r"""Test class for ItemsMetaschemaProperty class."""
    
    _mod = 'yggdrasil.metaschema.properties.JSONArrayMetaschemaProperties'
    _cls = 'ItemsMetaschemaProperty'
    
    @pytest.fixture(scope="class")
    def nele(self):
        r"""Number of elements in test arrays."""
        return 3

    @pytest.fixture(scope="class")
    def valid_value(self, nele):
        r"""Base class for valid arrays."""
        return [int(i) for i in range(nele)]

    @pytest.fixture(scope="class")
    def valid_sing(self):
        r"""Valid type for single element."""
        return {'type': 'int'}

    @pytest.fixture(scope="class")
    def valid_mult(self, nele, valid_sing):
        r"""Valid type for multiple elements."""
        return [valid_sing for _ in range(nele)]

    @pytest.fixture(scope="class")
    def invalid_sing(self):
        r"""Invalid type for single element."""
        return {'type': 'float'}

    @pytest.fixture(scope="class")
    def invalid_mult(self, nele, invalid_sing):
        r"""Inalid type for multiple elements."""
        return [invalid_sing for _ in range(nele)]

    @pytest.fixture(scope="class")
    def valid(self, nele, valid_value, valid_sing, valid_mult):
        r"""Objects that are valid."""
        return [(valid_value, valid_sing),
                (valid_value, valid_mult),
                ([int(i) for i in range(nele - 1)], valid_sing)]

    @pytest.fixture(scope="class")
    def invalid(self, nele, valid_sing, valid_mult):
        r"""Objects that are invalid."""
        return [([float(i) for i in range(nele)], valid_sing),
                ([float(i) for i in range(nele)], valid_mult)]

    @pytest.fixture(scope="class")
    def valid_compare(self, nele, valid_sing, valid_mult):
        r"""Objects that successfully compare."""
        return [(valid_sing, valid_sing),
                (valid_sing, valid_mult),
                (valid_mult, valid_sing),
                (valid_mult, valid_mult)]

    @pytest.fixture(scope="class")
    def invalid_compare(self, valid_sing, invalid_sing,
                        valid_mult, invalid_mult):
        r"""Objects that do not successfully compare."""
        return [(valid_sing, invalid_sing),
                (valid_sing, invalid_mult),
                (valid_mult, invalid_sing),
                (valid_mult, invalid_mult),
                (1, 1),
                (valid_mult, valid_mult[:-1])]
