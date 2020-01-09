import copy
import numpy as np
from yggdrasil import units, platform
from yggdrasil.metaschema.datatypes.tests import test_MetaschemaType as parent
from yggdrasil.metaschema.properties.ScalarMetaschemaProperties import (
    _valid_types)


class TestScalarMetaschemaType(parent.TestMetaschemaType):
    r"""Test class for ScalarMetaschemaType class with float."""
    _mod = 'ScalarMetaschemaType'
    _cls = 'ScalarMetaschemaType'
    _prec = 32
    _type = 'float'
    _shape = 1
    _array_contents = None

    @staticmethod
    def after_class_creation(cls):
        r"""Actions to be taken during class construction."""
        parent.TestMetaschemaType.after_class_creation(cls)
        if not cls._explicit:
            cls._typedef['subtype'] = cls._type
        if cls._type == 'bytes':
            dtype = 'S%d' % (cls._prec // 8)
        elif cls._type == 'unicode':
            dtype = 'U%d' % (cls._prec // 32)
        else:
            dtype = '%s%d' % (cls._type, cls._prec)
        if cls._array_contents is None:
            cls._array = np.ones(cls._shape, dtype)
        else:
            cls._array = np.array(cls._array_contents, dtype)
        if cls._type in ['bytes', 'unicode']:
            dtype_invalid = 'float'
        else:
            dtype_invalid = 'S10'
        cls._invalid_array = np.ones(cls._shape, dtype_invalid)
        if 'Array' not in cls._cls:
            cls._value = cls._array[0]
            cls._invalid_decoded.append(cls._array)
            cls._invalid_decoded.append(cls._invalid_array[0])
        else:
            cls._value = cls._array
            if cls._array.ndim == 1:
                cls._invalid_decoded.append(cls._array[0])
                cls._invalid_decoded.append(np.ones((3, 4), dtype))
            else:
                cls._invalid_decoded.append(cls._array[0][0])
                cls._invalid_decoded.append(cls._array[0])
            cls._invalid_decoded.append(cls._invalid_array)
        cls._valid_encoded = [{'type': cls.get_import_cls().name,
                               'precision': cls._prec,
                               'units': '',
                               'data': cls._value.tobytes()}]
        if not cls._explicit:
            cls._valid_encoded[0]['subtype'] = cls._type
        cls._valid_decoded = [cls._value]
        if cls._type == 'bytes':
            new_dtype = 'S%d' % (cls._prec * 2 // 8)
        elif cls._type == 'unicode':
            new_dtype = 'U%d' % (cls._prec * 2 // 32)
        else:
            new_dtype = '%s%d' % (cls._type, cls._prec * 2)
        if platform._is_win and (new_dtype == 'float128'):  # pragma: windows
            cls._prec_value = None
        else:
            prec_array = cls._array.astype(new_dtype)
            if 'Array' not in cls._cls:
                cls._prec_value = prec_array[0]
            else:
                cls._prec_value = prec_array
        cls._compatible_objects = [
            (cls._value, cls._value, None)]
        if cls._prec_value is not None:
            if not cls._explicit:
                cls._compatible_objects.append(
                    (cls._value, cls._prec_value, {'subtype': cls._type,
                                                   'precision': cls._prec * 2}))
            else:
                cls._compatible_objects.append(
                    (cls._value, cls._prec_value, {'precision': cls._prec * 2}))
        if 'Array' not in cls._cls:
            if cls._explicit:
                if cls._type == 'bytes':
                    cls._valid_normalize = [(1, b'1'),
                                            (u'1', b'1')]
                elif cls._type == 'unicode':
                    cls._valid_normalize = [(1, u'1'),
                                            (b'1', u'1')]
                else:
                    cls._valid_normalize = [(str(cls._value), cls._value),
                                            ('hello', 'hello')]
        if cls._explicit and ('Array' not in cls._cls):
            cls._invalid_encoded.append({'type': 'scalar',
                                         'subtype': 'invalid'})
        cls._invalid_validate.append(np.array([None, 1, list()]))

    def test_from_array(self):
        r"""Test getting object from array."""
        test_val = self._value
        test_kws = {}
        if 'units' in self._typedef:
            test_val = units.add_units(test_val, self._typedef['units'])
            test_kws['unit_str'] = self._typedef['units']
        self.assert_equal(self.instance.from_array(self._array, **test_kws),
                          test_val)


# Dynamically create tests for dynamic and explicitly typed scalars
for t in _valid_types.keys():
    iattr_imp = {'_type': t}
    if t == 'complex':
        iattr_imp['_prec'] = 64
    elif t in ('bytes', 'unicode'):
        iattr_imp['_array_contents'] = ['one', 'two', 'three']
        max_len = len(max(iattr_imp['_array_contents'], key=len))
        if t == 'unicode':
            iattr_imp['_prec'] = max_len * 32
        else:
            iattr_imp['_prec'] = max_len * 8
    iattr_exp = copy.deepcopy(iattr_imp)
    iattr_exp['_cls'] = '%sMetaschemaType' % t.title()
    iattr_exp['_explicit'] = True
    if t == 'float':
        iattr_exp['_prec'] = 64
    cls_imp = type('TestScalarMetaschemaType_%s' % t,
                   (TestScalarMetaschemaType, ), iattr_imp)
    cls_exp = type('Test%s' % iattr_exp['_cls'],
                   (TestScalarMetaschemaType, ), iattr_exp)
    globals()[cls_imp.__name__] = cls_imp
    globals()[cls_exp.__name__] = cls_exp
    del cls_imp, cls_exp


class TestScalarMetaschemaType_prec(TestScalarMetaschemaType):
    r"""Test class for ScalarMetaschemaType class with precision."""

    @staticmethod
    def after_class_creation(cls):
        r"""Actions to be taken during class construction."""
        TestScalarMetaschemaType.after_class_creation(cls)
        cls._typedef['precision'] = cls._prec
        cls._valid_encoded.append(copy.deepcopy(cls._valid_encoded[0]))
        for x in cls._invalid_encoded:
            x['precision'] = cls._prec / 2  # compatible precision
        # Version with incorrect precision
        cls._invalid_encoded.append(copy.deepcopy(cls._valid_encoded[0]))
        if cls._prec_value is not None:
            cls._invalid_encoded[-1]['precision'] = cls._prec * 2
            cls._invalid_decoded.append(cls._prec_value)


class TestScalarMetaschemaType_units(TestScalarMetaschemaType):
    r"""Test class for ScalarMetaschemaType class with units."""

    @staticmethod
    def after_class_creation(cls):
        r"""Actions to be taken during class construction."""
        TestScalarMetaschemaType.after_class_creation(cls)
        cls._typedef['units'] = 'cm'
        cls._valid_encoded.append(copy.deepcopy(cls._valid_encoded[0]))
        cls._valid_encoded[-1]['units'] = 'cm'
        cls._valid_encoded.append(copy.deepcopy(cls._valid_encoded[0]))
        cls._valid_encoded[-1]['units'] = 'm'
        cls._valid_decoded.append(copy.deepcopy(cls._valid_decoded[0]))
        cls._valid_decoded[-1] = units.add_units(cls._valid_decoded[-1], 'm')
        # Version with incorrect units
        cls._invalid_encoded.append(copy.deepcopy(cls._valid_encoded[0]))
        cls._invalid_encoded[-1]['units'] = 's'
