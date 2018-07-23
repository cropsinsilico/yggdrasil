import copy
import numpy as np
from cis_interface import units
from cis_interface.datatypes.tests import test_CisBaseType as parent


class TestCisScalarType(parent.TestCisBaseType):
    r"""Test class for CisScalarType class with float."""
    _mod = 'CisArrayType'
    _cls = 'CisScalarType'
    _prec = 32
    _type = 'float'
    _shape = 1
    _array_contents = None

    def __init__(self, *args, **kwargs):
        super(TestCisScalarType, self).__init__(*args, **kwargs)
        self._typedef = {'type': self._type}
        if self._type == 'string':
            dtype = 'S%d' % (self._prec / 8)
        else:
            dtype = '%s%d' % (self._type, self._prec)
        if self._array_contents is None:
            self._array = np.ones(self._shape, dtype)
        else:
            self._array = np.array(self._array_contents, dtype)
        if self._cls == 'CisScalarType':
            self._value = self._array[0]
        else:
            self._value = self._array
        self._valid_encoded = [{'typename': self.import_cls.name,
                                'type': self._type,
                                'precision': self._prec,
                                'units': '',
                                'data': self._value.tobytes()}]
        self._valid_decoded = [self._value]
        if self._type == 'string':
            new_dtype = 'S%d' % (self._prec * 2 / 8)
        else:
            new_dtype = '%s%d' % (self._type, self._prec * 2)
        prec_array = self._array.astype(new_dtype)
        if self._cls == 'CisScalarType':
            self._prec_value = prec_array[0]
        else:
            self._prec_value = prec_array
        self._compatible_objects = [
            (self._value, self._value, None),
            (self._value, self._prec_value, {'type': self._type,
                                             'precision': self._prec * 2})]


class TestCisScalarType_int(TestCisScalarType):
    r"""Test class for CisScalarType class with int."""
    _type = 'int'


class TestCisScalarType_uint(TestCisScalarType):
    r"""Test class for CisScalarType class with uint."""
    _type = 'uint'


class TestCisScalarType_complex(TestCisScalarType):
    r"""Test class for CisScalarType class with complex."""
    _type = 'complex'
    _prec = 64


class TestCisScalarType_string(TestCisScalarType):
    r"""Test class for CisScalarType class with string."""
    _type = 'string'
    _array_contents = ['one', 'two', 'three']


class TestCisScalarType_prec(TestCisScalarType):
    r"""Test class for CisScalarType class with precision."""

    def __init__(self, *args, **kwargs):
        super(TestCisScalarType_prec, self).__init__(*args, **kwargs)
        self._typedef['precision'] = self._prec
        self._valid_encoded.append(copy.deepcopy(self._valid_encoded[0]))
        self._invalid_encoded[-1]['precision'] = self._prec / 2
        # Version with incorrect precision
        self._invalid_encoded.append(copy.deepcopy(self._valid_encoded[0]))
        self._invalid_encoded[-1]['precision'] = self._prec * 2
        self._invalid_decoded.append(self._prec_value)


class TestCisScalarType_units(TestCisScalarType):
    r"""Test class for CisScalarType class with units."""

    def __init__(self, *args, **kwargs):
        super(TestCisScalarType_units, self).__init__(*args, **kwargs)
        self._typedef['units'] = 'cm'
        # self._valid_encoded[-1]['units'] = 'cm'
        self._valid_encoded.append(copy.deepcopy(self._valid_encoded[0]))
        self._valid_encoded[-1]['units'] = 'cm'
        self._valid_encoded.append(copy.deepcopy(self._valid_encoded[0]))
        self._valid_encoded[-1]['units'] = 'm'
        self._valid_decoded.append(copy.deepcopy(self._valid_decoded[0]))
        self._valid_decoded[-1] = units.add_units(self._valid_decoded[-1], 'm')
        # Version with incorrect units
        self._invalid_encoded.append(copy.deepcopy(self._valid_encoded[0]))
        self._invalid_encoded[-1]['units'] = 's'


class TestCis1DArrayType(TestCisScalarType):
    r"""Test class for CisArrayType class."""
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
    _cls = 'CisNDArrayType'
    _shape = (4, 5)

    def __init__(self, *args, **kwargs):
        super(TestCisNDArrayType, self).__init__(*args, **kwargs)
        self._valid_encoded[0]['shape'] = list(self._array.shape)

    def assert_result_equal(self, x, y):
        r"""Assert that serialized/deserialized objects equal."""
        np.testing.assert_array_equal(x, y)
