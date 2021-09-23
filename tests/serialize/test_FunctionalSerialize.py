import numpy as np
import unittest
from yggdrasil.serialize import DefaultSerialize
from yggdrasil.serialize.tests import test_SerializeBase as parent


class TestFunctionalSerialize(parent.TestSerializeBase):
    r"""Test class for FunctionalSerialize."""

    _cls = 'FunctionalSerialize'
    testing_option_kws = {'as_format': True}
    
    def __init__(self, *args, **kwargs):
        super(TestFunctionalSerialize, self).__init__(*args, **kwargs)
        self.func_serialize = self._func_serialize
        self.func_deserialize = self._func_deserialize

    def get_options(self):
        r"""Get testing options."""
        out = {'kwargs': {'func_serialize': self.func_serialize,
                          'func_deserialize': self.func_deserialize},
               'empty': b'',
               'objects': [['one', np.int32(1), 1.0],
                           ['two', np.int32(2), 1.0]],
               'extra_kwargs': {},
               'typedef': {'type': 'bytes'},
               'dtype': None,
               'is_user_defined': True}
        return out
        
    def _func_serialize(self, args):  # pragma: no cover
        r"""Method that serializes using repr."""
        return repr(args).encode("utf-8")

    def _func_deserialize(self, args):  # pragma: no cover
        r"""Method that deserializes using eval."""
        if len(args) == 0:
            return self.testing_options['empty']
        x = eval(args.decode("utf-8"))
        return x

    def test_serialize_sinfo(self):
        r"""Test serialize/deserialize with serializer info."""
        self.assert_raises(RuntimeError, self.instance.serialize,
                           self.testing_options['objects'][0],
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

    def get_options(self):
        r"""Get testing options."""
        temp_seri = FakeSerializer()
        assert(issubclass(temp_seri.__class__, DefaultSerialize.DefaultSerialize))
        out = super(TestFunctionalSerialize_class, self).get_options()
        out['kwargs'] = {'func_serialize': temp_seri,
                         'func_deserialize': temp_seri,
                         'encoded_datatype': {'type': 'bytes'}}
        return out
        

class TestFunctionalSerialize_error(TestFunctionalSerialize):
    r"""Test class for FunctionalSerialize class with incorrect functions."""

    def _func_serialize(self, args):
        r"""Method that serializes using repr."""
        return args

    def test_serialize(self):
        r"""Test serialize with function that dosn't return correct type."""
        self.assert_raises(TypeError, self.instance.serialize, (1,))

    @unittest.skipIf(True, 'Error testing')
    def test_serialize_no_metadata(self):
        r"""Test serializing without metadata."""
        pass  # pragma: no cover
        
    @unittest.skipIf(True, 'Error testing')
    def test_serialize_header(self):
        r"""Disabled: Test serialize/deserialize with header."""
        pass  # pragma: no cover

    @unittest.skipIf(True, 'Error testing')
    def test_serialize_sinfo(self):
        r"""Disabled: Test serialize/deserialize with serializer info."""
        pass  # pragma: no cover

    @unittest.skipIf(True, 'Error testing')
    def test_field_specs(self):
        r"""Disabled: Test field specifiers."""
        pass  # pragma: no cover
