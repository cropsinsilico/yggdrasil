import pytest
from tests.metaschema.datatypes.test_MetaschemaType import (
    TestMetaschemaType as base_class)
from yggdrasil.metaschema import MetaschemaTypeError
from yggdrasil.metaschema.datatypes.MultiMetaschemaType import (
    create_multitype_class)


class TestMultiMetaschemaType(base_class):
    r"""Test class for MultiMetaschemaType class."""

    _mod = 'yggdrasil.metaschema.datatypes.MultiMetaschemaType'
    _cls = 'MultiMetaschemaType'

    @pytest.fixture(scope="class")
    def types(self):
        r"""list: Test types."""
        return ['object', 'int']
    
    @pytest.fixture(scope="class", autouse=True)
    def python_class(self, types):
        r"""Python class that is being tested."""
        return create_multitype_class(types)

    @pytest.fixture(scope="class")
    def value(self):
        r"""dict: Test value."""
        return {'a': int(1), 'b': float(1)}
        
    @pytest.fixture(scope="class")
    def valid_encoded(self, typedef_base, types):
        r"""list: Encoded objects that are valid under this type."""
        return [dict(typedef_base, type=types)]

    @pytest.fixture(scope="class")
    def valid_decoded(self, value):
        r"""list: Objects that are valid under this type."""
        return [value, int(1)]

    @pytest.fixture(scope="class")
    def invalid_decoded(self):
        r"""list: Objects that are invalid under this type."""
        return ['hello']

    @pytest.fixture(scope="class")
    def compatible_objects(self, value):
        r"""list: Objects that are compatible with this type."""
        return [(value, value, None)]

    @pytest.fixture(scope="class")
    def typedef(self, typedef_base, types):
        r"""dict: Type definition"""
        return dict(typedef_base, type=types)

    def test_type_mismatch_error(self, python_class):
        r"""Test that error is raised when there is a type mismatch."""
        with pytest.raises(MetaschemaTypeError):
            python_class(type=['invalid'])
