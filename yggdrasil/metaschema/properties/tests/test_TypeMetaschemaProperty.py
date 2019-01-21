import numpy as np
from yggdrasil.metaschema.properties.tests import (
    test_MetaschemaProperty as parent)


class TestTypeMetaschemaProperty(parent.TestMetaschemaProperty):
    r"""Test class for TypeMetaschemaProperty class."""
    
    _mod = 'TypeMetaschemaProperty'
    _cls = 'TypeMetaschemaProperty'
    
    def __init__(self, *args, **kwargs):
        super(TestTypeMetaschemaProperty, self).__init__(*args, **kwargs)
        self._valid = [(np.int8(1), 'int'), (np.int8(1), 'scalar')]
        self._invalid = [(np.int8(1), 'float'), (np.float32(1), 'int')]
        self._encode_errors = [np]  # Can't encode modules
        self._valid_compare = [('int', 'int'), ('int', 'scalar'),
                               ('ply', 'object')]
        self._invalid_compare = [('int', 'float'), ('array', 'object'),
                                 ('ply', 'array'), ('1darray', 'scalar')]
