import pytest
from tests.metaschema.datatypes.test_MetaschemaType import (
    TestMetaschemaType as base_class)
import numpy as np


class TestJSONBooleanMetaschemaType(base_class):
    r"""Test class for JSONBooleanMetaschemaType class."""
    
    _mod = 'yggdrasil.metaschema.datatypes.JSONMetaschemaType'
    _cls = 'JSONBooleanMetaschemaType'

    @pytest.fixture(scope="class")
    def valid_encoded(self, python_class):
        r"""list: Encoded objects that are valid under this type."""
        return [{'type': python_class.name}]

    @pytest.fixture(scope="class")
    def valid_decoded(self):
        r"""list: Objects that are valid under this type."""
        return [True, False]
    
    @pytest.fixture(scope="class")
    def valid_normalize(self):
        r"""list: Pairs of pre-/post-normalized objects."""
        return [('True', True), ('true', True),
                ('False', False), ('false', False),
                ('hello', 'hello')]


class TestJSONIntegerMetaschemaType(TestJSONBooleanMetaschemaType):
    r"""Test class for JSONIntegerMetaschemaType class."""
    
    _cls = 'JSONIntegerMetaschemaType'

    @pytest.fixture(scope="class")
    def valid_decoded(self):
        r"""list: Objects that are valid under this type."""
        return [int(1), np.int(1)]
    
    @pytest.fixture(scope="class")
    def valid_normalize(self):
        r"""list: Pairs of pre-/post-normalized objects."""
        return [('1', 1), ('hello', 'hello')]


class TestJSONNullMetaschemaType(TestJSONBooleanMetaschemaType):
    r"""Test class for JSONNullMetaschemaType class."""
    
    _cls = 'JSONNullMetaschemaType'

    @pytest.fixture(scope="class")
    def valid_decoded(self):
        r"""list: Objects that are valid under this type."""
        return [None]
    
    @pytest.fixture(scope="class")
    def invalid_validate(self):
        r"""list: Objects that are invalid under this type."""
        return ['hello']

    @pytest.fixture(scope="class")
    def valid_normalize(self):
        r"""list: Pairs of pre-/post-normalized objects."""
        return []


class TestJSONNumberMetaschemaType(TestJSONBooleanMetaschemaType):
    r"""Test class for JSONNumberMetaschemaType class."""
    
    _cls = 'JSONNumberMetaschemaType'

    @pytest.fixture(scope="class")
    def valid_decoded(self):
        r"""list: Objects that are valid under this type."""
        return [int(1), np.int(1), float(1), np.float(1)]
        
    @pytest.fixture(scope="class")
    def valid_normalize(self):
        r"""list: Pairs of pre-/post-normalized objects."""
        return [('1', 1.0), ('1.0', 1.0), ('hello', 'hello')]


class TestJSONStringMetaschemaType(TestJSONBooleanMetaschemaType):
    r"""Test class for JSONStringMetaschemaType class."""
    
    _cls = 'JSONStringMetaschemaType'

    @pytest.fixture(scope="class")
    def valid_decoded(self):
        r"""list: Objects that are valid under this type."""
        return ['hello']
    
    @pytest.fixture(scope="class")
    def valid_normalize(self):
        r"""list: Pairs of pre-/post-normalized objects."""
        return [(1, '1'), (1.0, '1.0'), ([1, 2, 3], [1, 2, 3])]
