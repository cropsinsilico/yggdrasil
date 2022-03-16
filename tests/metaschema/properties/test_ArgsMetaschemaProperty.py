import pytest
from tests.metaschema.properties.test_MetaschemaProperty import (
    TestMetaschemaProperty as base_class)
import weakref


class DummyMeta(type):  # pragma: debug
    
    def __eq__(self, solf):
        import inspect
        a_str = f"{self.__module__}.{self.__name__}[{inspect.getfile(self)}]"
        b_str = f"{solf.__module__}.{solf.__name__}[{inspect.getfile(solf)}]"
        return a_str == b_str

    def __hash__(self):
        import inspect
        return hash(f"{self.__module__}.{self.__name__}[{inspect.getfile(self)}]")


class Dummy(metaclass=DummyMeta):  # pragma: debug
    pass


class ValidArgsClass1(metaclass=DummyMeta):
    test_args = tuple([int(0), Dummy])
    test_kwargs = dict(c=int(1), d=Dummy)
    valid_args = [{'type': 'int'}, {'type': 'class'}]
    valid_kwargs = {'c': {'type': 'int'},
                    'd': {'type': 'class'}}
    invalid_args = [{'type': 'int'}, {'type': 'float'}]
    invalid_kwargs = {'c': {'type': 'float'},
                      'd': {'type': 'float'}}

    def __init__(self, a, b, c=0, d=Dummy):
        self.b = b
        self.d = d
        self._input_args = tuple([a, weakref.ref(b)])
        self._input_kwargs = {'c': c, 'd': weakref.ref(d)}
        
    def __eq__(self, solf):
        if solf.__class__ != self.__class__:  # pragma: debug
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


class TestArgsMetaschemaProperty(base_class):
    r"""Test class for ArgsMetaschemaProperty class."""
    
    _mod = 'yggdrasil.metaschema.properties.ArgsMetaschemaProperty'
    _cls = 'ArgsMetaschemaProperty'

    @pytest.fixture(scope="class")
    def valid_classes(self):
        return [ValidArgsClass1, ValidArgsClass2,
                ValidArgsClass3, ValidArgsClass4]

    @pytest.fixture(scope="class")
    def valid_instances(self, valid_classes):
        return [cls(*(cls.test_args), **(cls.test_kwargs))
                for cls in valid_classes]
    
    @pytest.fixture(scope="class")
    def valid(self, valid_instances):
        r"""Objects that are valid."""
        return [(x, x.__class__.valid_args) for x in valid_instances]

    @pytest.fixture(scope="class")
    def invalid(self, valid_instances):
        r"""Objects that are invalid."""
        return [(x, x.__class__.invalid_args) for x in valid_instances]

    @pytest.fixture(scope="class")
    def valid_type(self, valid_classes):
        r"""Valid type."""
        return valid_classes[0].valid_args
    
    @pytest.fixture(scope="class")
    def invalid_type(self, valid_classes):
        r"""Invalid type."""
        return valid_classes[0].invalid_args

    @pytest.fixture(scope="class")
    def encode_errors(self):
        r"""Object that enduce errors during encoding."""
        return [int(1), InvalidArgsClass]

    @pytest.fixture(scope="class")
    def valid_compare(self, valid_type):
        r"""Objects that successfully compare."""
        return [(valid_type, valid_type)]

    @pytest.fixture(scope="class")
    def invalid_compare(self, valid_type, invalid_type):
        r"""Objects that do not successfully compare."""
        return [(valid_type, invalid_type)]
