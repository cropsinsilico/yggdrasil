import pytest
from tests.metaschema.datatypes.test_MetaschemaType import (
    TestMetaschemaType as base_class)
from yggdrasil.metaschema.datatypes.FunctionMetaschemaType import example_func


class TestFunctionMetaschemaType(base_class):
    r"""Test class for FunctionMetaschemaType class with float."""

    _mod = 'yggdrasil.metaschema.datatypes.FunctionMetaschemaType'
    _cls = 'FunctionMetaschemaType'

    @pytest.fixture(scope="class")
    def value(self):
        r"""function: Test function."""
        return example_func
    
    @pytest.fixture(scope="class")
    def valid_encoded(self, python_class, typedef_base):
        r"""list: Encoded objects that are valid under this type."""
        return [dict(typedef_base,
                     type=python_class.name)]
    
    @pytest.fixture(scope="class")
    def valid_decoded(self, value):
        r"""list: Objects that are valid under this type."""
        return [value]
    
    @pytest.fixture(scope="class")
    def invalid_decoded(self):
        r"""list: Objects that are invalid under this type."""
        return [object]

    @pytest.fixture(scope="class")
    def compatible_objects(self, value):
        r"""list: Objects that are compatible with this type."""
        return [(value, value, None)]

    @pytest.fixture(scope="class")
    def valid_normalize(self):
        r"""list: Pairs of pre-/post-normalized objects."""
        return [(None, None),
                ('yggdrasil.metaschema.datatypes.FunctionMetaschemaType'
                 ':example_func', example_func)]

    def test_decode_data_errors(self, python_class):
        r"""Test errors in decode_data."""
        with pytest.raises(ValueError):
            python_class.decode_data('hello', None)
        with pytest.raises(AttributeError):
            python_class.decode_data('yggdrasil:invalid', None)
