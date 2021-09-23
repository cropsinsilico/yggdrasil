import pytest
from tests.metaschema.datatypes.test_MetaschemaType import (
    TestMetaschemaType as base_class)
from tests.metaschema.properties.test_ArgsMetaschemaProperty import (
    ValidArgsClass4, InvalidArgsClass)


class TestInstanceMetaschemaType(base_class):
    r"""Test class for InstanceMetaschemaType class."""

    _mod = 'yggdrasil.metaschema.datatypes.InstanceMetaschemaType'
    _cls = 'InstanceMetaschemaType'

    @pytest.fixture(scope="class")
    def typedef_base(self):
        r"""dict: Base type definition."""
        return {'class': ValidArgsClass4,
                'args': ValidArgsClass4.valid_args,
                'kwargs': ValidArgsClass4.valid_kwargs}
    
    @pytest.fixture(scope="class")
    def value(self):
        r"""object: Test instance."""
        return ValidArgsClass4(*ValidArgsClass4.test_args,
                               **ValidArgsClass4.test_kwargs)

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
        return [int(1), 'hello']

    @pytest.fixture(scope="class")
    def invalid_validate(self):
        r"""list: Objects that are invalid under this type."""
        return [None, InvalidArgsClass()]

    @pytest.fixture(scope="class")
    def compatible_objects(self, value):
        r"""list: Objects that are compatible with this type."""
        return [(value, value, None)]

    @pytest.fixture
    def nested_result(self, nested_approx):
        r"""Prepare value for comparison."""
        def nested_result_w(x):
            if isinstance(x, ValidArgsClass4):
                return x
            return nested_approx(x)
        return nested_result_w
