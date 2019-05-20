from yggdrasil.tests import assert_raises
from yggdrasil.metaschema.datatypes.tests import test_MetaschemaType as parent


class TestAnyMetaschemaType(parent.TestMetaschemaType):
    r"""Test class for AnyMetaschemaType class."""

    _mod = 'AnyMetaschemaType'
    _cls = 'AnyMetaschemaType'

    def __init__(self, *args, **kwargs):
        super(TestAnyMetaschemaType, self).__init__(*args, **kwargs)
        self._value = {'a': int(1), 'b': float(1)}
        self._valid_encoded = [dict(self.typedef,
                                    temptype={'type': 'int'})]
        self._valid_decoded = [self._value, object]
        self._invalid_validate = []
        self._invalid_encoded = [{}]
        self._invalid_decoded = []
        self._compatible_objects = [(self._value, self._value, None)]

    def test_decode_data_errors(self):
        r"""Test errors in decode_data."""
        assert_raises(ValueError, self.import_cls.decode_data, 'hello', None)
