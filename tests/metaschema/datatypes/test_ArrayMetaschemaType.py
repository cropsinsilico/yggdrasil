import pytest
import copy
import numpy as np
from yggdrasil import units
from tests.metaschema.datatypes.test_ScalarMetaschemaType import (
    TestScalarMetaschemaType as base_class)


class TestOneDArrayMetaschemaType(base_class):
    r"""Test class for ArrayMetaschemaType class."""
    
    _mod = 'yggdrasil.metaschema.datatypes.ArrayMetaschemaType'
    _cls = 'OneDArrayMetaschemaType'

    @pytest.fixture(scope="class")
    def explicit(self):
        r"""bool: If True the type is explicit."""
        return False

    @pytest.fixture(scope="class")
    def subtype(self):
        r"""str: Scalar base type."""
        return "float"
    
    @pytest.fixture(scope="class")
    def shape(self):
        r"""int,tuple: Shape of scalar/array."""
        return 10
    
    @pytest.fixture(scope="class")
    def valid_decoded(self, value, valid_units, dtype):
        r"""list: Objects that are valid under this type."""
        out = [value]
        for x in valid_units:
            out.append(units.add_units(copy.deepcopy(out[0]), x))
        out.append(np.array([], dtype))
        return out


class TestNDArrayMetaschemaType(base_class):
    r"""Test class for ArrayMetaschemaType class with 2D array."""

    _mod = 'yggdrasil.metaschema.datatypes.ArrayMetaschemaType'
    _cls = 'NDArrayMetaschemaType'

    @pytest.fixture(scope="class")
    def explicit(self):
        r"""bool: If True the type is explicit."""
        return False

    @pytest.fixture(scope="class")
    def subtype(self):
        r"""str: Scalar base type."""
        return "float"
    
    @pytest.fixture(scope="class")
    def shape(self):
        r"""int,tuple: Shape of scalar/array."""
        return (4, 5)
