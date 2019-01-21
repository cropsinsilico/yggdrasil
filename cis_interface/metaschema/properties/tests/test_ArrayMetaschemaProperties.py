import numpy as np
from yggdrasil import units
from yggdrasil.metaschema.properties.tests import (
    test_MetaschemaProperty as parent)


class TestLengthMetaschemaProperty(parent.TestMetaschemaProperty):
    r"""Test class for LengthMetaschemaProperty class."""
    
    _mod = 'ArrayMetaschemaProperties'
    _cls = 'LengthMetaschemaProperty'
    
    def __init__(self, *args, **kwargs):
        super(TestLengthMetaschemaProperty, self).__init__(*args, **kwargs)
        nele = 3
        valid = np.zeros(nele, 'float')
        self._valid = [(valid, nele), (units.add_units(valid, 'cm'), nele)]
        self._invalid = [(valid, nele - 1)]
        self._valid_compare = [(nele, nele)]
        self._invalid_compare = [(nele - 1, nele), (nele, nele - 1)]


class TestShapeMetaschemaProperty(parent.TestMetaschemaProperty):
    r"""Test class for ShapeMetaschemaProperty class."""
    
    _mod = 'ArrayMetaschemaProperties'
    _cls = 'ShapeMetaschemaProperty'
    
    def __init__(self, *args, **kwargs):
        super(TestShapeMetaschemaProperty, self).__init__(*args, **kwargs)
        nele = (3, 4)
        valid = np.zeros(nele, 'float')
        self._valid = [(valid, nele), (units.add_units(valid, 'cm'), nele)]
        self._invalid = [(valid, (nele[0], nele[1] - 1))]
        self._valid_compare = [(nele, nele),
                               (nele, list(nele))]
        self._invalid_compare = [(nele, nele[::-1]),
                                 (nele, nele[:-1])]
