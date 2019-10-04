from yggdrasil.metaschema.datatypes.tests import (
    test_JSONObjectMetaschemaType as parent)


class TestSchemaMetaschemaType(parent.TestJSONObjectMetaschemaType):
    r"""Test class for SchemaMetaschemaType class."""

    _mod = 'SchemaMetaschemaType'
    _cls = 'SchemaMetaschemaType'

    @staticmethod
    def after_class_creation(cls):
        r"""Actions to be taken during class construction."""
        parent.TestJSONObjectMetaschemaType.after_class_creation(cls)
        cls._value = cls._fulldef
        cls._fulldef = {'type': 'schema'}
        cls._typedef = {'type': 'schema'}
        cls._valid_encoded = [cls._fulldef]
        cls._valid_decoded = [cls._value]
        cls._invalid_validate = [None]
        cls._invalid_decoded = [{}]
        cls._invalid_encoded = [{}]
        cls._compatible_objects = [(cls._value, cls._value, None)]
        cls._valid_normalize += [('float', {'type': 'float',
                                            'precision': 64}),
                                 ({'units': 'g'}, {'units': 'g',
                                                   'type': 'scalar',
                                                   'subtype': 'float',
                                                   'precision': 64}),
                                 ({'title': 'a'}, {'title': 'a'}),
                                 ({'title': 'a', 'units': 'g'},
                                  {'title': 'a', 'units': 'g',
                                   'type': 'scalar', 'subtype': 'float',
                                   'precision': 64}),
                                 ({}, {})]
