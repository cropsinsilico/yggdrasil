import pytest
import numpy as np
from yggdrasil import units
from yggdrasil.metaschema import MetaschemaTypeError
from tests.metaschema.properties.test_MetaschemaProperty import (
    TestMetaschemaProperty as base_class)


class TestSubtypeMetaschemaProperty(base_class):
    r"""Test class for SubtypeMetaschemaProperty class."""
    
    _mod = 'yggdrasil.metaschema.properties.ScalarMetaschemaProperties'
    _cls = 'SubtypeMetaschemaProperty'
    
    @pytest.fixture(scope="class")
    def valid(self):
        r"""Objects that are valid."""
        return [(int(1), 'int'), (float(1), 'float')]

    @pytest.fixture(scope="class")
    def invalid(self):
        r"""Objects that are invalid."""
        return [(int(1), 'float'), (float(1), 'int')]

    @pytest.fixture(scope="class")
    def valid_compare(self):
        r"""Objects that successfully compare."""
        return [('int', 'int')]

    @pytest.fixture(scope="class")
    def invalid_compare(self):
        r"""Objects that do not successfully compare."""
        return [('float', 'int')]

    @pytest.fixture(scope="class")
    def valid_normalize_schema(self):
        r"""Schemas for normalization."""
        return [
            ({'subtype': 'float'}, {'subtype': 'float'}),
            ({'units': 'g'}, {'units': 'g', 'subtype': 'float'}),
            ({'units': ''}, {'units': ''})]

    def test_invalid_encode(self, python_class):
        r"""Test invalid encode for object dtype."""
        with pytest.raises(MetaschemaTypeError):
            python_class.encode(object)


class TestPrecisionMetaschemaProperty(base_class):
    r"""Test class for PrecisionMetaschemaProperty class."""
    
    _mod = 'yggdrasil.metaschema.properties.ScalarMetaschemaProperties'
    _cls = 'PrecisionMetaschemaProperty'
    
    @pytest.fixture(scope="class")
    def valid(self):
        r"""Objects that are valid."""
        return [(np.int32(1), 32), (np.float16(1), 16)]

    @pytest.fixture(scope="class")
    def invalid(self):
        r"""Objects that are invalid."""
        return [(np.int32(1), 8), (np.float32(1), 16)]

    @pytest.fixture(scope="class")
    def valid_compare(self):
        r"""Objects that successfully compare."""
        return [(32, 32), (16, 32)]

    @pytest.fixture(scope="class")
    def invalid_compare(self):
        r"""Objects that do not successfully compare."""
        return [(32, 16)]

    @pytest.fixture(scope="class")
    def valid_normalize_schema(self):
        r"""Schemas for normalization."""
        return [
            ({'precision': 64}, {'precision': 64}),
            ({'subtype': 'int'}, {'subtype': 'int', 'precision': 64}),
            ({'subtype': 'complex'}, {'subtype': 'complex', 'precision': 128})]


class TestUnitsMetaschemaProperty(base_class):
    r"""Test class for UnitsMetaschemaProperty class."""
    
    _mod = 'yggdrasil.metaschema.properties.ScalarMetaschemaProperties'
    _cls = 'UnitsMetaschemaProperty'
    
    @pytest.fixture(scope="class")
    def valid(self):
        r"""Objects that are valid."""
        return [(1, ''), (units.add_units(1, 'cm'), 'm')]

    @pytest.fixture(scope="class")
    def invalid(self):
        r"""Objects that are invalid."""
        return [(units.add_units(1, 'cm'), 'kg')]

    @pytest.fixture(scope="class")
    def valid_compare(self):
        r"""Objects that successfully compare."""
        return [('cm', 'cm'), ('cm', 'm'), ('m', 'cm'), ('', 'cm'), ('cm', '')]

    @pytest.fixture(scope="class")
    def invalid_compare(self):
        r"""Objects that do not successfully compare."""
        return [('cm', 'g')]
