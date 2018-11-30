import numpy as np
import nose.tools as nt
from cis_interface import units
from cis_interface.metaschema.properties import ScalarMetaschemaProperties
from cis_interface.metaschema.properties.tests import (
    test_MetaschemaProperty as parent)


def test_definition2dtype_errors():
    r"""Check that error raised if type not specified."""
    nt.assert_raises(KeyError, ScalarMetaschemaProperties.definition2dtype, {})


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
