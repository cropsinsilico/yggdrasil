from yggdrasil.metaschema.properties.tests import (
    test_MetaschemaProperty as parent)


class TestTemptypeMetaschemaProperty(parent.TestMetaschemaProperty):
    r"""Test class for TemptypeMetaschemaProperty class."""
    
    _mod = 'AnyMetaschemaProperties'
    _cls = 'TemptypeMetaschemaProperty'
    
    def __init__(self, *args, **kwargs):
        super(TestTemptypeMetaschemaProperty, self).__init__(*args, **kwargs)
        # valid_type = {'a': {'type': 'int'}, 'b': {'type': 'int'}}
        # invalid_type = {'a': {'type': 'int'}, 'b': {'type': 'float'}}
        self._valid = [(int(1), {'type': 'int'}),
                       ([int(1), float(1)],
                        {'type': 'array',
                         'items': [{'type': 'int'}, {'type': 'float'}]}),
                       ({'a': int(1), 'b': float(2)},
                        {'type': 'object',
                         'properties': {
                             'a': {'type': 'int'},
                             'b': {'type': 'float'}}})]
        self._invalid = [(int(1), {'type': 'float'})]
        self._valid_compare = [({'type': 'int'}, {'type': 'int'})]
        self._invalid_compare = [({'type': 'int'}, {'type': 'float'})]
