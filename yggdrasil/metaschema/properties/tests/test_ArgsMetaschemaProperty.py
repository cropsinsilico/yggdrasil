from yggdrasil.metaschema.properties.tests import (
    test_MetaschemaProperty as parent)


class ValidArgsClass1(object):
    test_args = tuple([int(0), int(1)])
    test_kwargs = dict()
    valid_args_prop = {'a': {'type': 'int'},
                       'b': {'type': 'int'}}
    invalid_args_prop = {'a': {'type': 'int'},
                         'b': {'type': 'float'}}

    def __init__(self, a, b):
        self._input_args = {'a': int(a), 'b': int(b)}
        
    def __eq__(self, solf):
        if not isinstance(solf, self.__class__):  # pragma: debug
            return False
        return (self._input_args == solf._input_args)


class ValidArgsClass2(ValidArgsClass1):
    def get_input_args(self):
        return self._input_args


class ValidArgsClass3(ValidArgsClass2):
    @property
    def input_arguments(self):
        return self._input_args


class ValidArgsClass4(ValidArgsClass1):
    test_args = tuple([int(0), int(1)])
    test_kwargs = dict(c=int(1))
    valid_args_prop = {'args': {'type': 'array',
                                'items': [{'type': 'int'},
                                          {'type': 'int'}]},
                       'kwargs': {'type': 'object',
                                  'properties': {
                                      'c': {'type': 'int'}}}}
    invalid_args_prop = {'args': {'type': 'array',
                                  'items': [{'type': 'int'},
                                            {'type': 'float'}]},
                         'kwargs': {'type': 'object',
                                    'properties': {
                                        'c': {'type': 'int'}}}}

    def __init__(self, *args, **kwargs):
        self._input_args = {'args': args, 'kwargs': kwargs}


class InvalidArgsClass:  # pragma: no cover
    # Old style class dosn't inherit from object
    pass


class TestArgsMetaschemaProperty(parent.TestMetaschemaProperty):
    r"""Test class for ArgsMetaschemaProperty class."""
    
    _mod = 'ArgsMetaschemaProperty'
    _cls = 'ArgsMetaschemaProperty'
    
    def __init__(self, *args, **kwargs):
        super(TestArgsMetaschemaProperty, self).__init__(*args, **kwargs)
        self._valid = []
        self._invalid = []
        for cls in [ValidArgsClass1, ValidArgsClass2,
                    ValidArgsClass3, ValidArgsClass4]:
            cls_inst = cls(*(cls.test_args), **(cls.test_kwargs))
            self._valid.append((cls_inst, cls.valid_args_prop))
            self._invalid.append((cls_inst, cls.invalid_args_prop))
        valid_type = {'args': {'type': 'array',
                               'items': [{'type': 'int'},
                                         {'type': 'int'}]},
                      'kwargs': {'type': 'object'}}
        invalid_type = {'args': {'type': 'array',
                                 'items': [{'type': 'int'},
                                           {'type': 'float'}]},
                        'kwargs': {'type': 'object'}}
        self._encode_errors = [int(1), InvalidArgsClass]
        self._valid_compare = [(valid_type, valid_type)]
        self._invalid_compare = [(valid_type, invalid_type)]
