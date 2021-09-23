import pytest
from tests.metaschema.datatypes.test_MetaschemaType import (
    TestMetaschemaType as base_class)


class TestAnyMetaschemaType(base_class):
    r"""Test class for AnyMetaschemaType class."""

    _mod = 'yggdrasil.metaschema.datatypes.AnyMetaschemaType'
    _cls = 'AnyMetaschemaType'

    @pytest.fixture(scope="class")
    def value(self):
        r"""dict: Test value."""
        return {'a': int(1), 'b': float(1)}

    @pytest.fixture(scope="class")
    def valid_encoded(self, typedef_base, value, python_class):
        r"""list: Encoded objects that are valid under this type."""
        return [dict(typedef_base,
                     type=python_class.name,
                     temptype={'type': 'int'})]
    
    @pytest.fixture(scope="class")
    def valid_decoded(self, value):
        r"""list: Objects that are valid under this type."""
        return [value, object]
        
    @pytest.fixture(scope="class")
    def invalid_validate(self):
        r"""list: Objects that are invalid under this type."""
        return []
    
    @pytest.fixture(scope="class")
    def invalid_encoded(self):
        r"""list: Encoded objects that are invalid under this type."""
        return []

    @pytest.fixture(scope="class")
    def compatible_objects(self, value):
        r"""list: Objects that are compatible with this type."""
        return [(value, value, None)]
    
    def test_decode_data_errors(self, python_class):
        r"""Test errors in decode_data."""
        with pytest.raises(ValueError):
            python_class.decode_data('hello', None)
