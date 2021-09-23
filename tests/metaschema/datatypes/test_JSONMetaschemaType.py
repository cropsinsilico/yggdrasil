import numpy as np
from yggdrasil.metaschema.datatypes.tests import test_MetaschemaType as parent


class TestJSONBooleanMetaschemaType(parent.TestMetaschemaType):
    r"""Test class for JSONBooleanMetaschemaType class."""
    
    _mod = 'JSONMetaschemaType'
    _cls = 'JSONBooleanMetaschemaType'

    @staticmethod
    def after_class_creation(cls):
        r"""Actions to be taken during class construction."""
        parent.TestMetaschemaType.after_class_creation(cls)
        cls._valid_encoded = [{'type': cls.get_import_cls().name}]
        cls._valid_decoded = [True, False]
        cls._invalid_validate = [None]
        cls._invalid_decoded = []
        cls._valid_normalize = [('True', True), ('true', True),
                                ('False', False), ('false', False),
                                ('hello', 'hello')]


class TestJSONIntegerMetaschemaType(TestJSONBooleanMetaschemaType):
    r"""Test class for JSONIntegerMetaschemaType class."""
    
    _cls = 'JSONIntegerMetaschemaType'

    @staticmethod
    def after_class_creation(cls):
        r"""Actions to be taken during class construction."""
        TestJSONBooleanMetaschemaType.after_class_creation(cls)
        cls._valid_decoded = [int(1), np.int(1)]
        cls._invalid_validate = [None]
        cls._invalid_decoded = []
        cls._valid_normalize = [('1', 1), ('hello', 'hello')]


class TestJSONNullMetaschemaType(TestJSONBooleanMetaschemaType):
    r"""Test class for JSONNullMetaschemaType class."""
    
    _cls = 'JSONNullMetaschemaType'

    @staticmethod
    def after_class_creation(cls):
        r"""Actions to be taken during class construction."""
        TestJSONBooleanMetaschemaType.after_class_creation(cls)
        cls._valid_decoded = [None]
        cls._invalid_validate = ['hello']
        cls._invalid_decoded = []
        cls._valid_normalize = []


class TestJSONNumberMetaschemaType(TestJSONBooleanMetaschemaType):
    r"""Test class for JSONNumberMetaschemaType class."""
    
    _cls = 'JSONNumberMetaschemaType'

    @staticmethod
    def after_class_creation(cls):
        r"""Actions to be taken during class construction."""
        TestJSONBooleanMetaschemaType.after_class_creation(cls)
        cls._valid_decoded = [int(1), np.int(1), float(1), np.float(1)]
        cls._invalid_validate = [None]
        cls._invalid_decoded = []
        cls._valid_normalize = [('1', 1.0), ('1.0', 1.0), ('hello', 'hello')]


class TestJSONStringMetaschemaType(TestJSONBooleanMetaschemaType):
    r"""Test class for JSONStringMetaschemaType class."""
    
    _cls = 'JSONStringMetaschemaType'

    @staticmethod
    def after_class_creation(cls):
        r"""Actions to be taken during class construction."""
        TestJSONBooleanMetaschemaType.after_class_creation(cls)
        cls._valid_decoded = ['hello']
        cls._invalid_validate = [None]
        cls._invalid_decoded = []
        cls._valid_normalize = [(1, '1'), (1.0, '1.0'),
                                ([1, 2, 3], [1, 2, 3])]
