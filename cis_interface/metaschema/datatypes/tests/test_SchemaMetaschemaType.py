from cis_interface.metaschema.datatypes.tests import (
    test_JSONObjectMetaschemaType as parent)


class TestSchemaMetaschemaType(parent.TestJSONObjectMetaschemaType):
    r"""Test class for SchemaMetaschemaType class."""

    _mod = 'SchemaMetaschemaType'
    _cls = 'SchemaMetaschemaType'

    def __init__(self, *args, **kwargs):
        super(TestSchemaMetaschemaType, self).__init__(*args, **kwargs)
        self._value = self._fulldef
        self._fulldef = {'type': 'schema'}
        self._typedef = {'type': 'schema'}
        self._valid_encoded = [self._fulldef]
        self._valid_decoded = [self._value]
        self._invalid_validate = [None]
        self._invalid_decoded = [{}]
        self._invalid_encoded = [{}]
        self._compatible_objects = [(self._value, self._value, None)]
        self._valid_normalize += [('float', {'type': 'float'}),
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
