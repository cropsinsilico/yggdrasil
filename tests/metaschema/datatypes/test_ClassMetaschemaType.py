import pytest
from tests.metaschema.datatypes.test_MetaschemaType import (
    TestMetaschemaType as base_class)
from yggdrasil.metaschema.datatypes.ClassMetaschemaType import ExampleClass
import os
import tempfile


class TestClassMetaschemaType(base_class):
    r"""Test class for ClassMetaschemaType class."""

    _mod = 'yggdrasil.metaschema.datatypes.ClassMetaschemaType'
    _cls = 'ClassMetaschemaType'

    @pytest.fixture(scope="class")
    def value(self):
        r"""type: Test class."""
        return ExampleClass
    
    @pytest.fixture(scope="class")
    def valid_encoded(self, python_class, typedef_base):
        r"""list: Encoded objects that are valid under this type."""
        return [dict(typedef_base,
                     type=python_class.name)]
    
    @pytest.fixture(scope="class")
    def valid_decoded(self, value):
        r"""list: Objects that are valid under this type."""
        return [value, object]
    
    @pytest.fixture(scope="class")
    def invalid_decoded(self):
        r"""list: Objects that are invalid under this type."""
        return ['hello']

    @pytest.fixture(scope="class")
    def compatible_objects(self, value):
        r"""list: Objects that are compatible with this type."""
        return [(value, value, None)]

    @pytest.fixture(scope="class")
    def valid_normalize(self):
        r"""list: Pairs of pre-/post-normalized objects."""
        return [(None, None),
                ('yggdrasil.metaschema.datatypes.ClassMetaschemaType:'
                 'ExampleClass', ExampleClass)]

    def test_module_file(self, python_class):
        r"""Test decoding data that includes the full path to the module file."""
        _tmpclassfile = os.path.join(tempfile.gettempdir(), 'test_class.py')
        with open(_tmpclassfile, 'w') as fd:
            fd.write('class ValidClass2(object):\n    pass\n')
        out = python_class.decode_data('%s:ValidClass2' % _tmpclassfile, None)
        assert(out.__name__ == 'ValidClass2')

    def test_decode_data_errors(self, python_class):
        r"""Test errors in decode_data."""
        with pytest.raises(ValueError):
            python_class.decode_data('hello', None)
        with pytest.raises(ImportError):
            python_class.decode_data('invalid:invalid', None)
        with pytest.raises(AttributeError):
            python_class.decode_data('yggdrasil:invalid', None)
