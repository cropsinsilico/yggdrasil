import os
import tempfile
from yggdrasil.tests import assert_raises
from yggdrasil.metaschema.datatypes.tests import test_MetaschemaType as parent


class ValidClass(object):  # pragma: debug
    r"""Valid class for testing."""
    pass


class TestClassMetaschemaType(parent.TestMetaschemaType):
    r"""Test class for ClassMetaschemaType class."""

    _mod = 'ClassMetaschemaType'
    _cls = 'ClassMetaschemaType'

    def __init__(self, *args, **kwargs):
        super(TestClassMetaschemaType, self).__init__(*args, **kwargs)
        self._value = ValidClass
        self._valid_encoded = [self.typedef]
        self._valid_decoded = [self._value, object]
        self._invalid_encoded = [{}]
        self._invalid_decoded = ['hello']
        self._compatible_objects = [(self._value, self._value, None)]
        self._valid_normalize += [('%s:ValidClass' % __name__, ValidClass)]

    def test_module_file(self):
        r"""Test decoding data that includes the full path to the module file."""
        _tmpclassfile = os.path.join(tempfile.gettempdir(), 'test_class.py')
        with open(_tmpclassfile, 'w') as fd:
            fd.write('class ValidClass2(object):\n    pass\n')
        out = self.import_cls.decode_data('%s:ValidClass2' % _tmpclassfile, None)
        self.assert_equal(out.__name__, 'ValidClass2')

    def test_decode_data_errors(self):
        r"""Test errors in decode_data."""
        assert_raises(ValueError, self.import_cls.decode_data, 'hello', None)
        assert_raises(ImportError, self.import_cls.decode_data, 'invalid:invalid', None)
        assert_raises(AttributeError, self.import_cls.decode_data,
                      'yggdrasil:invalid', None)
