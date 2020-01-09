from yggdrasil.metaschema.properties.tests import (
    test_MetaschemaProperty as parent)


class ValidArgsClass1(object):
    test_args = tuple([int(0), int(1)])
    test_kwargs = dict(c=int(1))
    valid_args = [{'type': 'int'}, {'type': 'int'}]
    valid_kwargs = {'c': {'type': 'int'}}
    invalid_args = [{'type': 'int'}, {'type': 'float'}]
    invalid_kwargs = {'c': {'type': 'float'}}

    def __init__(self, a, b, c=0):
        self._input_args = tuple([a, b])
        self._input_kwargs = {'c': c}
        
    def __eq__(self, solf):
        if not isinstance(solf, self.__class__):  # pragma: debug
            return False
        return ((self._input_args == solf._input_args)
                and (self._input_kwargs == solf._input_kwargs))


class ValidArgsClass2(ValidArgsClass1):
    def get_input_args(self):
        return self._input_args

    def get_input_kwargs(self):
        return self._input_kwargs
    

class ValidArgsClass3(ValidArgsClass2):
    @property
    def input_arguments(self):
        return self._input_args

    @property
    def input_keyword_arguments(self):
        return self._input_kwargs


class ValidArgsClass4(ValidArgsClass1):

    def __init__(self, *args, **kwargs):
        self._input_args = args
        self._input_kwargs = kwargs


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
            self._valid.append((cls_inst, cls.valid_args))
            self._invalid.append((cls_inst, cls.invalid_args))
        valid_type = ValidArgsClass1.valid_args
        invalid_type = ValidArgsClass1.invalid_args
        self._encode_errors = [int(1), InvalidArgsClass]
        self._valid_compare = [(valid_type, valid_type)]
        self._invalid_compare = [(valid_type, invalid_type)]
