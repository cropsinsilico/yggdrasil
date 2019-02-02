import numpy as np
from cis_interface.metaschema.datatypes.tests import test_MetaschemaType as parent


class TestJSONBooleanMetaschemaType(parent.TestMetaschemaType):
    r"""Test class for JSONBooleanMetaschemaType class."""
    
    _mod = 'JSONMetaschemaType'
    _cls = 'JSONBooleanMetaschemaType'

    def __init__(self, *args, **kwargs):
        super(TestJSONBooleanMetaschemaType, self).__init__(*args, **kwargs)
        self._valid_encoded = [{'type': self.import_cls.name}]
        self._valid_decoded = [True, False]
        self._invalid_validate = [None]
        self._invalid_decoded = []
        self._valid_normalize = [('True', True), ('true', True),
                                 ('False', False), ('false', False),
                                 ('hello', 'hello')]


class TestJSONIntegerMetaschemaType(TestJSONBooleanMetaschemaType):
    r"""Test class for JSONIntegerMetaschemaType class."""
    
    _cls = 'JSONIntegerMetaschemaType'

    def __init__(self, *args, **kwargs):
        super(TestJSONIntegerMetaschemaType, self).__init__(*args, **kwargs)
        self._valid_decoded = [int(1), np.int(1)]
        self._invalid_validate = [None]
        self._invalid_decoded = []
        self._valid_normalize = [('1', 1), ('hello', 'hello')]


class TestJSONNullMetaschemaType(TestJSONBooleanMetaschemaType):
    r"""Test class for JSONNullMetaschemaType class."""
    
    _cls = 'JSONNullMetaschemaType'

    def __init__(self, *args, **kwargs):
        super(TestJSONNullMetaschemaType, self).__init__(*args, **kwargs)
        self._valid_decoded = [None]
        self._invalid_validate = ['hello']
        self._invalid_decoded = []
        self._valid_normalize = []


class TestJSONNumberMetaschemaType(TestJSONBooleanMetaschemaType):
    r"""Test class for JSONNumberMetaschemaType class."""
    
    _cls = 'JSONNumberMetaschemaType'

    def __init__(self, *args, **kwargs):
        super(TestJSONNumberMetaschemaType, self).__init__(*args, **kwargs)
        self._valid_decoded = [int(1), np.int(1), float(1), np.float(1)]
        self._invalid_validate = [None]
        self._invalid_decoded = []
        self._valid_normalize = [('1', 1.0), ('1.0', 1.0), ('hello', 'hello')]


class TestJSONStringMetaschemaType(TestJSONBooleanMetaschemaType):
    r"""Test class for JSONStringMetaschemaType class."""
    
    _cls = 'JSONStringMetaschemaType'

    def __init__(self, *args, **kwargs):
        super(TestJSONStringMetaschemaType, self).__init__(*args, **kwargs)
        self._valid_decoded = ['hello']
        self._invalid_validate = [None]
        self._invalid_decoded = []
        self._valid_normalize = [(1, '1'), (1.0, '1.0'),
                                 ([1, 2, 3], [1, 2, 3])]
