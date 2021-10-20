import pytest
import numpy as np
from tests.serialize import TestSerializeBase as base_class
from yggdrasil.serialize import DefaultSerialize


class TestFunctionalSerialize(base_class):
    r"""Test class for FunctionalSerialize."""

    @pytest.fixture(scope="class", autouse=True)
    def serializer(self):
        r"""str: Serializer being tested."""
        return "functional"

    @pytest.fixture(scope="class", autouse=True,
                    params=[{'as_format': True}])
    def options(self, request):
        r"""Arguments that should be provided when getting testing options."""
        return request.param

    @pytest.fixture(scope="class")
    def testing_options(self, func_serialize, func_deserialize):
        r"""Testing options."""
        out = {'kwargs': {'func_serialize': func_serialize,
                          'func_deserialize': func_deserialize},
               'empty': b'',
               'objects': [['one', np.int32(1), 1.0],
                           ['two', np.int32(2), 1.0]],
               'extra_kwargs': {},
               'typedef': {'type': 'bytes'},
               'dtype': None,
               'is_user_defined': True}
        return out
    
    @pytest.fixture(scope="class")
    def func_serialize(self):
        r"""Method that serializes using repr."""
        def func_serialize_w(args):
            return repr(args).encode("utf-8")
        return func_serialize_w

    @pytest.fixture(scope="class")
    def func_deserialize(self):
        r"""Method that deserializes using eval."""
        def func_deserialize_w(args):
            if len(args) == 0:
                return b''
            x = eval(args.decode("utf-8"))
            return x
        return func_deserialize_w

    def test_serialize_sinfo(self, instance, testing_options):
        r"""Test serialize/deserialize with serializer info."""
        with pytest.raises(RuntimeError):
            instance.serialize(testing_options['objects'][0],
                               add_serializer_info=True)
    

class FakeSerializer(DefaultSerialize.DefaultSerialize):
    r"""Fake serializer that mocks user defined serialization/deserialization
    routines."""

    _dont_register = True

    def func_serialize(self, args):  # pragma: no cover
        r"""Method that serializes using repr."""
        return repr(args).encode("utf-8")

    def func_deserialize(self, args):  # pragma: no cover
        r"""Method that deserializes using eval."""
        if len(args) == 0:
            return []
        x = eval(args.decode("utf-8"))
        return x


class TestFunctionalSerialize_class(TestFunctionalSerialize):
    r"""Test class for FunctionalSerialize class with classes."""

    @pytest.fixture(scope="class")
    def testing_options(self, func_serialize, func_deserialize):
        r"""Testing options."""
        temp_seri = FakeSerializer()
        assert(issubclass(temp_seri.__class__,
                          DefaultSerialize.DefaultSerialize))
        out = {'kwargs': {'func_serialize': temp_seri,
                          'func_deserialize': temp_seri,
                          'encoded_datatype': {'type': 'bytes'}},
               'empty': b'',
               'objects': [['one', np.int32(1), 1.0],
                           ['two', np.int32(2), 1.0]],
               'extra_kwargs': {},
               'typedef': {'type': 'bytes'},
               'dtype': None,
               'is_user_defined': True}
        return out
        

class TestFunctionalSerialize_error(TestFunctionalSerialize):
    r"""Test class for FunctionalSerialize class with incorrect functions."""

    test_serialize_no_metadata = None
    test_serialize_header = None
    test_serialize_sinfo = None
    test_field_specs = None

    @pytest.fixture(scope="class")
    def func_serialize(self):
        r"""Method that serializes using repr."""
        def func_serialize_w(args):
            return args
        return func_serialize_w

    def test_serialize(self, instance):
        r"""Test serialize with function that dosn't return correct type."""
        with pytest.raises(TypeError):
            instance.serialize((1,))
