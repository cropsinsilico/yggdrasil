from yggdrasil.metaschema.datatypes import MetaschemaTypeError
from yggdrasil.metaschema.datatypes.tests import test_MetaschemaType as parent
from yggdrasil.metaschema.datatypes.MultiMetaschemaType import (
    create_multitype_class)


class TestMultiMetaschemaType(parent.TestMetaschemaType):
    r"""Test class for MultiMetaschemaType class."""

    _mod = 'MultiMetaschemaType'
    _cls = 'MultiMetaschemaType'
    _types = ['object', 'int']
    
    @staticmethod
    def after_class_creation(cls):
        r"""Actions to be taken during class construction."""
        parent.TestMetaschemaType.after_class_creation(cls)
        cls._value = {'a': int(1), 'b': float(1)}
        cls._valid_encoded = [dict(cls._typedef,
                                   type=cls._types)]
        cls._valid_decoded = [cls._value, int(1)]
        cls._invalid_decoded = ['hello']
        cls._compatible_objects = [(cls._value, cls._value, None)]

    @property
    def import_cls(self):
        r"""Import the tested class from its module"""
        return create_multitype_class(self._types)
        
    @property
    def typedef(self):
        r"""dict: Type definition."""
        out = super(TestMultiMetaschemaType, self).typedef
        out['type'] = self._types
        return out

    def test_type_mismatch_error(self):
        r"""Test that error is raised when there is a type mismatch."""
        self.assert_raises(MetaschemaTypeError, self.import_cls,
                           type=['invalid'])
