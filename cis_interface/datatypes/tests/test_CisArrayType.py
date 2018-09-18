import numpy as np
from cis_interface.datatypes.tests.test_CisScalarType import TestCisScalarType


class TestCis1DArrayType(TestCisScalarType):
    r"""Test class for CisArrayType class."""
    _mod = 'CisArrayType'
    _cls = 'Cis1DArrayType'
    _shape = 10

    def __init__(self, *args, **kwargs):
        super(TestCis1DArrayType, self).__init__(*args, **kwargs)
        self._valid_encoded[0]['length'] = len(self._array)

    def assert_result_equal(self, x, y):
        r"""Assert that serialized/deserialized objects equal."""
        np.testing.assert_array_equal(x, y)
        

class TestCisNDArrayType(TestCisScalarType):
    r"""Test class for CisArrayType class with 2D array."""
    _mod = 'CisArrayType'
    _cls = 'CisNDArrayType'
    _shape = (4, 5)

    def __init__(self, *args, **kwargs):
        super(TestCisNDArrayType, self).__init__(*args, **kwargs)
        self._valid_encoded[0]['shape'] = list(self._array.shape)

    def assert_result_equal(self, x, y):
        r"""Assert that serialized/deserialized objects equal."""
        np.testing.assert_array_equal(x, y)
