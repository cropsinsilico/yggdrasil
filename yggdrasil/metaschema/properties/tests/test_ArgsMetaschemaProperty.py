from yggdrasil.metaschema.properties.tests import (
    test_MetaschemaProperty as parent)


class ValidArgsClass1(object):
    def __init__(self, a, b):
        self._input_args = {'a': int(a), 'b': int(b)}
        

class ValidArgsClass2(ValidArgsClass1):
    def get_input_args(self):
        return self._input_args
    

class ValidArgsClass3(ValidArgsClass2):
    @property
    def input_arguments(self):
        return self._input_args


class TestArgsMetaschemaProperty(parent.TestMetaschemaProperty):
    r"""Test class for ArgsMetaschemaProperty class."""
    
    _mod = 'ArgsMetaschemaProperty'
    _cls = 'ArgsMetaschemaProperty'
    
    def __init__(self, *args, **kwargs):
        super(TestArgsMetaschemaProperty, self).__init__(*args, **kwargs)
        valid_type = {'a': {'type': 'int'}, 'b': {'type': 'int'}}
        invalid_type = {'a': {'type': 'int'}, 'b': {'type': 'float'}}
        self._valid = [(ValidArgsClass1(0, 1), valid_type),
                       (ValidArgsClass2(0, 1), valid_type),
                       (ValidArgsClass3(0, 1), valid_type)]
        self._invalid = [(ValidArgsClass1(0, 1), invalid_type),
                         (ValidArgsClass2(0, 1), invalid_type),
                         (ValidArgsClass3(0, 1), invalid_type)]
        self._encode_errors = [int(1)]
        self._valid_compare = [(valid_type, valid_type)]
        self._invalid_compare = [(valid_type, invalid_type)]
