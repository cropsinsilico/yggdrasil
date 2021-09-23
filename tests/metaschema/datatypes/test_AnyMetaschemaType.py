from yggdrasil.tests import assert_raises
from yggdrasil.metaschema.datatypes.tests import test_MetaschemaType as parent


class TestAnyMetaschemaType(parent.TestMetaschemaType):
    r"""Test class for AnyMetaschemaType class."""

    _mod = 'AnyMetaschemaType'
    _cls = 'AnyMetaschemaType'
    
    @staticmethod
    def after_class_creation(cls):
        r"""Actions to be taken during class construction."""
        parent.TestMetaschemaType.after_class_creation(cls)
        cls._value = {'a': int(1), 'b': float(1)}
        cls._valid_encoded = [dict(cls._typedef,
                                   type=cls.get_import_cls().name,
                                   temptype={'type': 'int'})]
        cls._valid_decoded = [cls._value, object]
        cls._invalid_validate = []
        cls._invalid_encoded = [{}]
        cls._invalid_decoded = []
        cls._compatible_objects = [(cls._value, cls._value, None)]

    def test_decode_data_errors(self):
        r"""Test errors in decode_data."""
        assert_raises(ValueError, self.import_cls.decode_data, 'hello', None)
