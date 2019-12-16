from yggdrasil.tests import assert_raises
from yggdrasil.metaschema.datatypes.tests import test_MetaschemaType as parent


def valid_function():  # pragma: debug
    r"""Valid function for testing."""
    pass


class TestFunctionMetaschemaType(parent.TestMetaschemaType):
    r"""Test class for FunctionMetaschemaType class with float."""

    _mod = 'FunctionMetaschemaType'
    _cls = 'FunctionMetaschemaType'

    @staticmethod
    def after_class_creation(cls):
        r"""Actions to be taken during class construction."""
        parent.TestMetaschemaType.after_class_creation(cls)
        value = valid_function
        cls._valid_encoded = [dict(cls._typedef,
                                   type=cls.get_import_cls().name)]
        cls._valid_decoded = [value]
        cls._invalid_encoded = [{}]
        cls._invalid_decoded = [object]
        cls._compatible_objects = [(value, value, None)]
        cls._valid_normalize += [('%s:valid_function' % __name__, valid_function)]

    def test_decode_data_errors(self):
        r"""Test errors in decode_data."""
        assert_raises(ValueError, self.import_cls.decode_data, 'hello', None)
        assert_raises(AttributeError, self.import_cls.decode_data,
                      'yggdrasil:invalid', None)
