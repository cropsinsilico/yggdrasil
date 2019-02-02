import copy
import numpy as np
from yggdrasil import units
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

    def __init__(self, *args, **kwargs):
        super(TestScalarMetaschemaType, self).__init__(*args, **kwargs)
        if not self._explicit:
            self._typedef['subtype'] = self._type
        if self._type == 'bytes':
            dtype = 'S%d' % (self._prec // 8)
        elif self._type == 'unicode':
            dtype = 'U%d' % (self._prec // 32)
        else:
            dtype = '%s%d' % (self._type, self._prec)
        if self._array_contents is None:
            self._array = np.ones(self._shape, dtype)
        else:
            self._array = np.array(self._array_contents, dtype)
        if self._type in ['bytes', 'unicode']:
            dtype_invalid = 'float'
        else:
            dtype_invalid = 'S10'
        self._invalid_array = np.ones(self._shape, dtype_invalid)
        if 'Array' not in self._cls:
            self._value = self._array[0]
            self._invalid_decoded.append(self._array)
            self._invalid_decoded.append(self._invalid_array[0])
        else:
            self._value = self._array
            if self._array.ndim == 1:
                self._invalid_decoded.append(self._array[0])
                self._invalid_decoded.append(np.ones((3, 4), dtype))
            else:
                self._invalid_decoded.append(self._array[0][0])
                self._invalid_decoded.append(self._array[0])
            self._invalid_decoded.append(self._invalid_array)
        self._valid_encoded = [{'type': self.import_cls.name,
                                'precision': self._prec,
                                'units': '',
                                'data': self._value.tobytes()}]
        if not self._explicit:
            self._valid_encoded[0]['subtype'] = self._type
        self._valid_decoded = [self._value]
        if self._type == 'bytes':
            new_dtype = 'S%d' % (self._prec * 2 // 8)
        elif self._type == 'unicode':
            new_dtype = 'U%d' % (self._prec * 2 // 32)
        else:
            new_dtype = '%s%d' % (self._type, self._prec * 2)
        prec_array = self._array.astype(new_dtype)
        if 'Array' not in self._cls:
            self._prec_value = prec_array[0]
        else:
            self._prec_value = prec_array
        self._compatible_objects = [
            (self._value, self._value, None)]
        if not self._explicit:
            self._compatible_objects.append(
                (self._value, self._prec_value, {'subtype': self._type,
                                                 'precision': self._prec * 2}))
        else:
            self._compatible_objects.append(
                (self._value, self._prec_value, {'precision': self._prec * 2}))
        if 'Array' not in self._cls:
            if self._explicit:
                if self._type == 'bytes':
                    self._valid_normalize = [(1, b'1'),
                                             (u'1', b'1')]
                elif self._type == 'unicode':
                    self._valid_normalize = [(1, u'1'),
                                             (b'1', u'1')]
                else:
                    self._valid_normalize = [(str(self._value), self._value),
                                             ('hello', 'hello')]
        if self._explicit and ('Array' not in self._cls):
            self._invalid_encoded.append({'type': 'scalar',
                                          'subtype': 'invalid'})
        self._invalid_validate.append(np.array([None, 1, list()]))

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
    cls_imp = type('TestScalarMetaschemaType_%s' % t,
                   (TestScalarMetaschemaType, ), iattr_imp)
    cls_exp = type('Test%s' % iattr_exp['_cls'],
                   (TestScalarMetaschemaType, ), iattr_exp)
    globals()[cls_imp.__name__] = cls_imp
    globals()[cls_exp.__name__] = cls_exp
    del cls_imp, cls_exp


class TestScalarMetaschemaType_prec(TestScalarMetaschemaType):
    r"""Test class for ScalarMetaschemaType class with precision."""

    def __init__(self, *args, **kwargs):
        super(TestScalarMetaschemaType_prec, self).__init__(*args, **kwargs)
        self._typedef['precision'] = self._prec
        self._valid_encoded.append(copy.deepcopy(self._valid_encoded[0]))
        for x in self._invalid_encoded:
            x['precision'] = self._prec / 2  # compatible precision
        # Version with incorrect precision
        self._invalid_encoded.append(copy.deepcopy(self._valid_encoded[0]))
        self._invalid_encoded[-1]['precision'] = self._prec * 2
        self._invalid_decoded.append(self._prec_value)


class TestScalarMetaschemaType_units(TestScalarMetaschemaType):
    r"""Test class for ScalarMetaschemaType class with units."""

    def __init__(self, *args, **kwargs):
        super(TestScalarMetaschemaType_units, self).__init__(*args, **kwargs)
        self._typedef['units'] = 'cm'
        self._valid_encoded.append(copy.deepcopy(self._valid_encoded[0]))
        self._valid_encoded[-1]['units'] = 'cm'
        self._valid_encoded.append(copy.deepcopy(self._valid_encoded[0]))
        self._valid_encoded[-1]['units'] = 'm'
        self._valid_decoded.append(copy.deepcopy(self._valid_decoded[0]))
        self._valid_decoded[-1] = units.add_units(self._valid_decoded[-1], 'm')
        # Version with incorrect units
        self._invalid_encoded.append(copy.deepcopy(self._valid_encoded[0]))
        self._invalid_encoded[-1]['units'] = 's'
