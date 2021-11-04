import pytest
from tests.metaschema.datatypes.test_MetaschemaType import (
    TestMetaschemaType as base_class)
import copy
import numpy as np
from yggdrasil import units, platform, constants


class TestScalarMetaschemaType(base_class):
    r"""Test class for ScalarMetaschemaType class with float."""
    
    _mod = 'yggdrasil.metaschema.datatypes.ScalarMetaschemaType'
    _cls = 'ScalarMetaschemaType'

    @pytest.fixture(scope="class", params=[False, True])
    def explicit(self, request):
        r"""bool: If True the type is explicit."""
        return request.param

    @pytest.fixture(scope="class")
    def class_name(self, explicit, subtype):
        r"""Name of class that will be tested."""
        if not explicit:
            return self._cls
        return f"{subtype.title()}MetaschemaType"

    @pytest.fixture(scope="class")
    def precision(self, subtype, array_contents, explicit):
        r"""int: Precision to test."""
        if subtype == 'complex':
            return 64
        elif subtype in ['bytes', 'unicode']:
            max_len = len(max(array_contents, key=len))
            if subtype == 'unicode':
                return max_len * 32
            else:
                return max_len * 8
        elif explicit and (subtype == 'float'):
            return 64
        return 32

    @pytest.fixture(scope="class", params=list(constants.VALID_TYPES.keys()))
    def subtype(self, request):
        r"""str: Scalar base type."""
        return request.param

    @pytest.fixture(scope="class")
    def shape(self):
        r"""int,tuple: Shape of scalar/array."""
        return 1

    @pytest.fixture(scope="class")
    def value_units(self):
        r"""str: Units that should be added to the type definition."""
        return None

    @pytest.fixture(scope="class")
    def valid_units(self):
        r"""list: Units that are compatible with the typedef units."""
        return []

    @pytest.fixture(scope="class")
    def invalid_units(self):
        r"""list: Units that are NOT compatible with the typedef units."""
        return []

    @pytest.fixture(scope="class")
    def array_contents(self, subtype):
        r"""Array contents."""
        if subtype in ['bytes', 'unicode']:
            return ['one', 'two', 'three']
        return None
    
    @pytest.fixture(scope="class")
    def typedef_base(self, explicit, subtype, value_units):
        r"""dict: Base type definition."""
        out = {}
        if not explicit:
            out['subtype'] = subtype
        if value_units:
            out['units'] = value_units
        return out

    @pytest.fixture(scope="class")
    def dtype(self, subtype, precision):
        r"""str: Numpy Data type."""
        if subtype == 'bytes':
            return 'S%d' % (precision // 8)
        elif subtype == 'unicode':
            return 'U%d' % (precision // 32)
        else:
            return '%s%d' % (subtype, precision)

    @pytest.fixture(scope="class")
    def dtype_invalid(self, subtype):
        r"""str: Invalid numpy data type."""
        if subtype in ['bytes', 'unicode']:
            return 'float'
        else:
            return 'S10'

    @pytest.fixture(scope="class")
    def array(self, shape, dtype, array_contents):
        r"""np.ndarray: Array for testing."""
        if array_contents is None:
            return np.ones(shape, dtype)
        else:
            return np.array(array_contents, dtype)

    @pytest.fixture(scope="class")
    def invalid_array(self, shape, dtype_invalid):
        r"""np.ndarray: Invalid array."""
        return np.ones(shape, dtype_invalid)

    @pytest.fixture(scope="class")
    def value(self, class_name, array, value_units):
        r"""dict: Test value."""
        if 'Array' not in class_name:
            out = array[0]
        else:
            out = array
        if value_units:
            out = units.add_units(out, value_units)
        return out

    @pytest.fixture(scope="class")
    def invalid_decoded(self, class_name, array, invalid_array, dtype):
        r"""list: Objects that are invalid under this type."""
        out = []
        if 'Array' not in class_name:
            out += [array, invalid_array[0]]
        else:
            if array.ndim == 1:
                out += [array[0], np.ones((3, 4), dtype)]
            else:
                out += [array[0][0], array[0]]
            out.append(invalid_array)
        return out

    @pytest.fixture(scope="class")
    def valid_encoded(self, python_class, precision, value, explicit,
                      subtype, valid_units, shape):
        r"""list: Encoded objects that are valid under this type."""
        out = [{'type': python_class.name,
                'precision': precision,
                'units': '',
                'data': value.tobytes()}]
        if not explicit:
            out[0]['subtype'] = subtype
        for x in valid_units:
            out.append(dict(out[0], units=x))
        if isinstance(shape, tuple):
            out[0]['shape'] = shape
        elif shape > 1:
            out[0]['length'] = shape
        return out

    @pytest.fixture(scope="class")
    def valid_decoded(self, value, valid_units):
        r"""list: Objects that are valid under this type."""
        out = [value]
        for x in valid_units:
            out.append(units.add_units(copy.deepcopy(out[0]), x))
        return out
    
    @pytest.fixture(scope="class")
    def precision_value(self, class_name, subtype, precision, array):
        r"""np.ndarray: Value with specific precision."""
        if subtype == 'bytes':
            new_dtype = 'S%d' % (precision * 2 // 8)
        elif subtype == 'unicode':
            new_dtype = 'U%d' % (precision * 2 // 32)
        else:
            new_dtype = '%s%d' % (subtype, precision * 2)
        if platform._is_win and (new_dtype == 'float128'):  # pragma: windows
            return None
        else:
            prec_array = array.astype(new_dtype)
            if 'Array' not in class_name:
                return prec_array[0]
            else:
                return prec_array

    @pytest.fixture(scope="class")
    def compatible_objects(self, subtype, precision, explicit, value,
                           precision_value):
        r"""list: Objects that are compatible with this type."""
        out = [(value, value, None)]
        if precision_value is not None:
            if not explicit:
                out.append(
                    (value, precision_value, {'subtype': subtype,
                                              'precision': precision * 2}))
            else:
                out.append(
                    (value, precision_value, {'precision': precision * 2}))
        return out
            
    @pytest.fixture(scope="class")
    def valid_normalize(self, class_name, explicit, subtype, value):
        r"""list: Pairs of pre-/post-normalized objects."""
        if 'Array' not in class_name:
            if explicit:
                if subtype == 'bytes':
                    return [(1, b'1'), (u'1', b'1')]
                elif subtype == 'unicode':
                    return [(1, u'1'), (b'1', u'1')]
                else:
                    return [(str(value), value), ('hello', 'hello')]
        return []

    @pytest.fixture(scope="class")
    def invalid_encoded(self, class_name, explicit, invalid_units):
        r"""list: Encoded objects that are invalid under this type."""
        out = [{}]
        if explicit and ('Array' not in class_name):
            out.append({'type': 'scalar', 'subtype': 'invalid'})
        for x in invalid_units:
            out.append(dict(out[0], units=x))
        return out
            
    @pytest.fixture(scope="class")
    def invalid_validate(self):
        r"""list: Objects that are invalid under this type."""
        return [None, np.array([None, 1, list()], dtype=object)]

    def test_from_array(self, value, typedef_base, array, instance,
                        nested_approx):
        r"""Test getting object from array."""
        test_val = value
        test_kws = {}
        if 'units' in typedef_base:
            test_val = units.add_units(test_val, typedef_base['units'])
            test_kws['unit_str'] = typedef_base['units']
        assert(instance.from_array(array, **test_kws) == nested_approx(test_val))


class TestScalarMetaschemaType_prec(TestScalarMetaschemaType):
    r"""Test class for ScalarMetaschemaType class with precision."""

    @pytest.fixture(scope="class")
    def explicit(self):
        r"""bool: If True the type is explicit."""
        return False
    
    @pytest.fixture(scope="class")
    def subtype(self):
        r"""str: Scalar base type."""
        return "float"
    
    @pytest.fixture(scope="class")
    def typedef_base(self, explicit, subtype, precision):
        r"""dict: Base type definition."""
        return {'subtype': subtype,
                'precision': precision}
    
    @pytest.fixture(scope="class")
    def valid_encoded(self, python_class, precision, value, explicit,
                      subtype):
        r"""list: Encoded objects that are valid under this type."""
        out = [{'type': python_class.name,
                'precision': precision,
                'units': '',
                'data': value.tobytes(),
                'subtype': subtype}]
        # out.append(copy.deepcopy(out[0]))
        return out
    
    @pytest.fixture(scope="class")
    def invalid_encoded(self, precision, valid_encoded, precision_value):
        r"""list: Encoded objects that are invalid under this type."""
        out = [{'precision': precision / 2}]  # compatible precision
        out.append(copy.deepcopy(valid_encoded[0]))
        if precision_value is not None:
            out[-1]['precision'] = precision * 2
        return out
    
    @pytest.fixture(scope="class")
    def invalid_decoded(self, class_name, array, invalid_array, dtype,
                        precision_value):
        r"""list: Objects that are invalid under this type."""
        out = []
        if 'Array' not in class_name:
            out += [array, invalid_array[0]]
        else:
            if array.ndim == 1:
                out += [array[0], np.ones((3, 4), dtype)]
            else:
                out += [array[0][0], array[0]]
            out.append(invalid_array)
        if precision_value is not None:
            out.append(precision_value)
        return out


class TestScalarMetaschemaType_units(TestScalarMetaschemaType):
    r"""Test class for ScalarMetaschemaType class with units."""

    @pytest.fixture(scope="class")
    def explicit(self):
        r"""bool: If True the type is explicit."""
        return False
    
    @pytest.fixture(scope="class")
    def subtype(self):
        r"""str: Scalar base type."""
        return "float"
    
    @pytest.fixture(scope="class")
    def value_units(self, valid_units):
        r"""str: Units that should be added to the type definition."""
        return valid_units[0]
    
    @pytest.fixture(scope="class")
    def valid_units(self):
        r"""list: Units that are compatible with the typedef units."""
        return ['cm', 'm']

    @pytest.fixture(scope="class")
    def invalid_units(self):
        r"""list: Invalid units."""
        return ['s']
