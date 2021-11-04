import pytest
from tests.metaschema.properties.test_MetaschemaProperty import (
    TestMetaschemaProperty as base_class)
import numpy as np


class TestTypeMetaschemaProperty(base_class):
    r"""Test class for TypeMetaschemaProperty class."""
    
    _mod = 'yggdrasil.metaschema.properties.TypeMetaschemaProperty'
    _cls = 'TypeMetaschemaProperty'
    
    @pytest.fixture(scope="class")
    def valid(self):
        r"""Objects that are valid."""
        return [(np.int8(1), 'int'), (np.int8(1), 'scalar')]

    @pytest.fixture(scope="class")
    def invalid(self):
        r"""Objects that are invalid."""
        return [(np.int8(1), 'float'), (np.float32(1), 'int')]

    @pytest.fixture(scope="class")
    def encode_errors(self):
        r"""Object that enduce errors during encoding."""
        return [np]  # Can't encode modules

    @pytest.fixture(scope="class")
    def valid_compare(self):
        r"""Objects that successfully compare."""
        return [('int', 'int'), ('int', 'scalar'), ('ply', 'object')]

    @pytest.fixture(scope="class")
    def invalid_compare(self):
        r"""Objects that do not successfully compare."""
        return [('int', 'float'), ('array', 'object'),
                ('ply', 'array'), ('1darray', 'scalar')]
