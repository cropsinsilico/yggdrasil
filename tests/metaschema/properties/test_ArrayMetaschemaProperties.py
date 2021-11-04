import pytest
import numpy as np
from yggdrasil import units
from tests.metaschema.properties.test_MetaschemaProperty import (
    TestMetaschemaProperty as base_class)


class TestLengthMetaschemaProperty(base_class):
    r"""Test class for LengthMetaschemaProperty class."""
    
    _mod = 'yggdrasil.metaschema.properties.ArrayMetaschemaProperties'
    _cls = 'LengthMetaschemaProperty'
    
    @pytest.fixture(scope="class")
    def nele(self):
        r"""Number of elements in test arrays."""
        return 3

    @pytest.fixture(scope="class")
    def valid_base(self, nele):
        r"""Base class for valid arrays."""
        return np.zeros(nele, 'float')

    @pytest.fixture(scope="class")
    def valid(self, nele, valid_base):
        r"""Objects that are valid."""
        return [(valid_base, nele), (units.add_units(valid_base, 'cm'), nele)]

    @pytest.fixture(scope="class")
    def invalid(self, nele, valid_base):
        r"""Objects that are invalid."""
        return [(valid_base, nele - 1)]

    @pytest.fixture(scope="class")
    def valid_compare(self, nele):
        r"""Objects that successfully compare."""
        return [(nele, nele)]

    @pytest.fixture(scope="class")
    def invalid_compare(self, nele):
        r"""Objects that do not successfully compare."""
        return [(nele - 1, nele), (nele, nele - 1)]


class TestShapeMetaschemaProperty(TestLengthMetaschemaProperty):
    r"""Test class for ShapeMetaschemaProperty class."""
    
    _mod = 'yggdrasil.metaschema.properties.ArrayMetaschemaProperties'
    _cls = 'ShapeMetaschemaProperty'
    
    @pytest.fixture(scope="class")
    def nele(self):
        r"""Number of elements in test arrays."""
        return (3, 4)

    @pytest.fixture(scope="class")
    def invalid(self, nele, valid_base):
        r"""Objects that are invalid."""
        return [(valid_base, (nele[0], nele[1] - 1))]

    @pytest.fixture(scope="class")
    def valid_compare(self, nele):
        r"""Objects that successfully compare."""
        return [(nele, nele), (nele, list(nele))]

    @pytest.fixture(scope="class")
    def invalid_compare(self, nele):
        r"""Objects that do not successfully compare."""
        return [(nele, nele[::-1]), (nele, nele[:-1])]
