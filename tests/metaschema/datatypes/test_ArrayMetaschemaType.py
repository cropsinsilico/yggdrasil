import numpy as np
from yggdrasil.metaschema.datatypes.tests import (
    test_ScalarMetaschemaType as parent)


class TestOneDArrayMetaschemaType(parent.TestScalarMetaschemaType):
    r"""Test class for ArrayMetaschemaType class."""
    _mod = 'ArrayMetaschemaType'
    _cls = 'OneDArrayMetaschemaType'
    _shape = 10

    def __init__(self, *args, **kwargs):
        super(TestOneDArrayMetaschemaType, self).__init__(*args, **kwargs)
        self._valid_encoded[0]['length'] = len(self._array)
        self._valid_decoded.append(np.array([], self._array.dtype))

    @classmethod
    def assert_result_equal(cls, x, y):
        r"""Assert that serialized/deserialized objects equal."""
        np.testing.assert_array_equal(x, y)
        

class TestNDArrayMetaschemaType(parent.TestScalarMetaschemaType):
    r"""Test class for ArrayMetaschemaType class with 2D array."""
    _mod = 'ArrayMetaschemaType'
    _cls = 'NDArrayMetaschemaType'
    _shape = (4, 5)

    def __init__(self, *args, **kwargs):
        super(TestNDArrayMetaschemaType, self).__init__(*args, **kwargs)
        self._valid_encoded[0]['shape'] = list(self._array.shape)

    @classmethod
    def assert_result_equal(cls, x, y):
        r"""Assert that serialized/deserialized objects equal."""
        np.testing.assert_array_equal(x, y)
