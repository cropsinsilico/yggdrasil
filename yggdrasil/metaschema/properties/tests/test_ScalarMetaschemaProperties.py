import numpy as np
from yggdrasil import units
from yggdrasil.tests import assert_raises, assert_equal
from yggdrasil.metaschema.properties import ScalarMetaschemaProperties
from yggdrasil.metaschema.properties.tests import (
    test_MetaschemaProperty as parent)
from yggdrasil.metaschema.datatypes import MetaschemaTypeError


def test_data2dtype_errors():
    r"""Check that error is raised for list, dict, & tuple objects."""
    assert_raises(MetaschemaTypeError, ScalarMetaschemaProperties.data2dtype, [])


def test_definition2dtype_errors():
    r"""Check that error raised if type not specified."""
    assert_raises(KeyError, ScalarMetaschemaProperties.definition2dtype, {})
    assert_raises(RuntimeError, ScalarMetaschemaProperties.definition2dtype,
                  {'type': 'float'})
    assert_equal(ScalarMetaschemaProperties.definition2dtype({'type': 'bytes'}),
                 np.dtype((ScalarMetaschemaProperties._valid_types['bytes'])))


class TestSubtypeMetaschemaProperty(parent.TestMetaschemaProperty):
    r"""Test class for SubtypeMetaschemaProperty class."""
    
    _mod = 'ScalarMetaschemaProperties'
    _cls = 'SubtypeMetaschemaProperty'
    
    def __init__(self, *args, **kwargs):
        super(TestSubtypeMetaschemaProperty, self).__init__(*args, **kwargs)
        self._valid = [(int(1), 'int'), (float(1), 'float')]
        self._invalid = [(int(1), 'float'), (float(1), 'int')]
        self._valid_compare = [('int', 'int')]
        self._invalid_compare = [('float', 'int')]
        self._valid_normalize_schema = [
            ({'subtype': 'float'}, {'subtype': 'float'}),
            ({'units': 'g'}, {'units': 'g', 'subtype': 'float'}),
            ({'units': ''}, {'units': ''})]

    def test_invalid_encode(self):
        r"""Test invalid encode for object dtype."""
        assert_raises(MetaschemaTypeError, self.import_cls.encode, object)


class TestPrecisionMetaschemaProperty(parent.TestMetaschemaProperty):
    r"""Test class for PrecisionMetaschemaProperty class."""
    
    _mod = 'ScalarMetaschemaProperties'
    _cls = 'PrecisionMetaschemaProperty'
    
    def __init__(self, *args, **kwargs):
        super(TestPrecisionMetaschemaProperty, self).__init__(*args, **kwargs)
        self._valid = [(np.int32(1), 32), (np.float16(1), 16)]
        self._invalid = [(np.int32(1), 8), (np.float32(1), 16)]
        self._valid_compare = [(32, 32), (16, 32)]
        self._invalid_compare = [(32, 16)]
        self._valid_normalize_schema = [
            ({'precision': 64}, {'precision': 64}),
            ({'subtype': 'int'}, {'subtype': 'int', 'precision': 64}),
            ({'subtype': 'complex'}, {'subtype': 'complex', 'precision': 128})]


class TestUnitsMetaschemaProperty(parent.TestMetaschemaProperty):
    r"""Test class for UnitsMetaschemaProperty class."""
    
    _mod = 'ScalarMetaschemaProperties'
    _cls = 'UnitsMetaschemaProperty'
    
    def __init__(self, *args, **kwargs):
        super(TestUnitsMetaschemaProperty, self).__init__(*args, **kwargs)
        self._valid = [(1, ''), (units.add_units(1, 'cm'), 'm')]
        self._invalid = [(units.add_units(1, 'cm'), 'kg')]
        self._valid_compare = [('cm', 'cm'), ('cm', 'm'), ('m', 'cm'),
                               ('', 'cm'), ('cm', '')]
        self._invalid_compare = [('cm', 'g')]
