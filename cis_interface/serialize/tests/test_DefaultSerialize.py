import copy
import numpy as np
import unittest
from cis_interface.tests import CisTestClassInfo, assert_equal
from cis_interface import backwards, tools, serialize
from cis_interface.serialize import DefaultSerialize
from cis_interface.metaschema.datatypes import encode_type


def test_demote_string():
    r"""Test format str creation of typedef."""
    x = DefaultSerialize.DefaultSerialize(format_str='%s')
    assert_equal(x.typedef, {'type': 'array',
                             'items': [{'type': 'bytes'}]})


class TestDefaultSerialize(CisTestClassInfo):
    r"""Test class for DefaultSerialize class."""

    _cls = 'DefaultSerialize'
    _empty_msg = b''
    attr_list = (copy.deepcopy(CisTestClassInfo.attr_list)
                 + ['datatype', 'typedef', 'numpy_dtype'])

    def __init__(self, *args, **kwargs):
        super(TestDefaultSerialize, self).__init__(*args, **kwargs)
        self._header_info = dict(arg1='1', arg2='two')

    @property
    def mod(self):
        r"""Module for class to be tested."""
        return 'cis_interface.serialize.%s' % self.cls

    @property
    def inst_kwargs(self):
        r"""Keyword arguments for creating the test instance."""
        out = super(TestDefaultSerialize, self).inst_kwargs
        out.update(self.testing_options['kwargs'])
        return out

    def empty_head(self, msg):
        r"""dict: Empty header for message only contains the size."""
        out = dict(size=len(msg), incomplete=False)
        if msg == tools.CIS_MSG_EOF:  # pragma: debug
            out['eof'] = True
        return out

    def map_sent2recv(self, obj):
        r"""Convert a sent object into a received one."""
        return obj

    def assert_result_equal(self, x, y):
        r"""Assert that serialized/deserialized objects equal."""
        self.assert_equal(x, self.map_sent2recv(y))

    def test_field_specs(self):
        r"""Test field specifiers."""
        self.assert_equal(self.instance.is_user_defined,
                          self.testing_options.get('is_user_defined', False))
        self.assert_equal(self.instance.numpy_dtype,
                          self.testing_options['dtype'])
        self.assert_equal(self.instance.extra_kwargs,
                          self.testing_options['extra_kwargs'])
        self.assert_equal(self.instance.typedef,
                          self.testing_options['typedef'])
        if isinstance(self.instance.typedef.get('items', []), dict):
            self.assert_raises(Exception, self.instance.get_field_names)
            self.assert_raises(Exception, self.instance.get_field_units)
        else:
            self.assert_equal(self.instance.get_field_names(),
                              self.testing_options.get('field_names', None))
            self.assert_equal(self.instance.get_field_units(),
                              self.testing_options.get('field_units', None))
        
    def test_serialize(self):
        r"""Test serialize/deserialize."""
        for iobj in self.testing_options['objects']:
            msg = self.instance.serialize(iobj)
            iout, ihead = self.instance.deserialize(msg)
            self.assert_result_equal(iout, iobj)
            # self.assert_equal(ihead, self.empty_head(msg))

    def test_serialize_no_metadata(self):
        r"""Test serializing without metadata."""
        self.instance.serialize(self.testing_options['objects'][0],
                                no_metadata=True)

    def test_deserialize_error(self):
        r"""Test error when deserializing message that is not bytes."""
        self.assert_raises(TypeError, self.instance.deserialize, None)
        
    def test_serialize_sinfo(self):
        r"""Test serialize/deserialize with serializer info."""
        if self.testing_options.get('is_user_defined', False):
            self.assert_raises(RuntimeError, self.instance.serialize,
                               self.testing_options['objects'][0],
                               add_serializer_info=True)
        else:
            hout = copy.deepcopy(self._header_info)
            hout.update(self.instance.serializer_info)
            temp_seri = serialize.get_serializer(
                seritype=self.instance.serializer_info['seritype'])
            for iobj in self.testing_options['objects']:
                hout.update(encode_type(iobj, typedef=self.instance.typedef))
                msg = self.instance.serialize(iobj, header_kwargs=self._header_info,
                                              add_serializer_info=True)
                iout, ihead = self.instance.deserialize(msg)
                hout.update(size=ihead['size'], id=ihead['id'],
                            incomplete=False)
                self.assert_result_equal(iout, iobj)
                self.assert_equal(ihead, hout)
                # Use info to reconstruct serializer
                iout, ihead = temp_seri.deserialize(msg)
                self.assert_result_equal(iout, iobj)
                self.assert_equal(ihead, hout)
                new_seri = serialize.get_serializer(**ihead)
                iout, ihead = new_seri.deserialize(msg)
                self.assert_result_equal(iout, iobj)
                self.assert_equal(ihead, hout)
            
    def test_serialize_header(self):
        r"""Test serialize/deserialize with header."""
        for iobj in self.testing_options['objects']:
            msg = self.instance.serialize(iobj, header_kwargs=self._header_info)
            iout, ihead = self.instance.deserialize(msg)
            self.assert_result_equal(iout, iobj)
            # self.assert_equal(ihead, self._header_info)
        
    def test_serialize_eof(self):
        r"""Test serialize/deserialize EOF."""
        iobj = tools.CIS_MSG_EOF
        msg = self.instance.serialize(iobj)
        iout, ihead = self.instance.deserialize(msg)
        self.assert_equal(iout, iobj)
        # self.assert_equal(ihead, self.empty_head(msg))
        
    def test_serialize_eof_header(self):
        r"""Test serialize/deserialize EOF with header."""
        iobj = tools.CIS_MSG_EOF
        msg = self.instance.serialize(iobj, header_kwargs=self._header_info)
        iout, ihead = self.instance.deserialize(msg)
        self.assert_equal(iout, iobj)
        # self.assert_equal(ihead, self.empty_head(msg))
        
    def test_serialize_no_format(self):
        r"""Test serialize/deserialize without format string."""
        if (len(self._inst_kwargs) == 0) and (self._cls == 'DefaultSerialize'):
            for iobj in self.testing_options['objects']:
                msg = self.instance.serialize(iobj,
                                              header_kwargs=self._header_info)
                iout, ihead = self.instance.deserialize(msg)
                self.assert_result_equal(iout, iobj)
                # self.assert_equal(ihead, self._header_info)
            # self.assert_raises(Exception, self.instance.serialize, ['msg', 0])
        
    def test_deserialize_empty(self):
        r"""Test call for empty string."""
        out, head = self.instance.deserialize(self._empty_msg)
        self.assert_result_equal(out, self.testing_options['empty'])
        self.assert_equal(head, self.empty_head(self._empty_msg))

    def test_invalid_update(self):
        r"""Test error raised when serializer updated with type that isn't
        compatible."""
        if (len(self._inst_kwargs) == 0) and (self._cls == 'DefaultSerialize'):
            self.instance.initialize_from_message(np.int64(1))
            self.assert_raises(RuntimeError, self.instance.update_serializer,
                               type='ply')
        

class TestDefaultSerialize_format(TestDefaultSerialize):
    r"""Test class for DefaultSerialize class with format."""

    testing_option_kws = {'as_format': True}


class TestDefaultSerialize_array(TestDefaultSerialize_format):
    r"""Test class for DefaultSerialize class with format as array."""

    testing_option_kws = {'as_format': True, 'as_array': True}


class TestDefaultSerialize_uniform(TestDefaultSerialize):
    r"""Test class for items as dictionary."""
    
    def get_options(self):
        r"""Get testing options."""
        out = {'kwargs': {'type': 'array', 'items': {'type': '1darray',
                                                     'subtype': 'float',
                                                     'precision': 64}},
               # 'field_units': ['cm', 'g']},
               'empty': [],
               'objects': [[np.zeros(3, 'float'), np.zeros(3, 'float')],
                           [np.ones(3, 'float'), np.ones(3, 'float')]],
               'extra_kwargs': {},
               'typedef': {'type': 'array', 'items': {'type': '1darray',
                                                      'subtype': 'float',
                                                      'precision': 64}},
               'dtype': np.dtype("float64"),  # np.dtype([('f0', '<f8'), ('f1', '<f8')]),
               'is_user_defined': False}
        return out


class TestDefaultSerialize_uniform_names(TestDefaultSerialize_uniform):
    r"""Test class for items as dictionary."""
    
    def get_options(self):
        r"""Get testing options."""
        out = super(TestDefaultSerialize_uniform_names, self).get_options()
        out['kwargs']['field_names'] = [b'a', b'b']
        out['kwargs']['field_units'] = [b'cm', b'g']
        out['field_names'] = ['a', 'b']
        out['field_units'] = ['cm', 'g']
        out['dtype'] = np.dtype([('a', '<f8'), ('b', '<f8')])
        out['typedef'] = {'type': 'array',
                          'items': [{'type': '1darray',
                                     'subtype': 'float',
                                     'precision': 64,
                                     'title': 'a',
                                     'units': 'cm'},
                                    {'type': '1darray',
                                     'subtype': 'float',
                                     'precision': 64,
                                     'title': 'b',
                                     'units': 'g'}]}
        return out


class TestDefaultSerialize_func(TestDefaultSerialize):
    r"""Test class for DefaultSerialize class with functions."""

    testing_option_kws = {'as_format': True}
    
    def __init__(self, *args, **kwargs):
        super(TestDefaultSerialize_func, self).__init__(*args, **kwargs)
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
        return backwards.as_bytes(repr(args))

    def _func_deserialize(self, args):  # pragma: no cover
        r"""Method that deserializes using eval."""
        if len(args) == 0:
            return self.testing_options['empty']
        x = eval(backwards.as_str(args))
        return x


class FakeSerializer(DefaultSerialize.DefaultSerialize):

    def func_serialize(self, args):  # pragma: no cover
        r"""Method that serializes using repr."""
        return backwards.as_bytes(repr(args))

    def func_deserialize(self, args):  # pragma: no cover
        r"""Method that deserializes using eval."""
        if len(args) == 0:
            return []
        x = eval(backwards.as_str(args))
        return x


class TestDefaultSerialize_class(TestDefaultSerialize_func):
    r"""Test class for DefaultSerialize class with classes."""

    def get_options(self):
        r"""Get testing options."""
        temp_seri = FakeSerializer()
        assert(issubclass(temp_seri.__class__, DefaultSerialize.DefaultSerialize))
        out = super(TestDefaultSerialize_class, self).get_options()
        out['kwargs'] = {'func_serialize': temp_seri,
                         'func_deserialize': temp_seri,
                         'func_typedef': {'type': 'bytes'},
                         'encode_func_serialize': True,
                         'decode_func_deserialize': True}
        return out
        

class TestDefaultSerialize_alias(TestDefaultSerialize_format):
    r"""Test class for DefaultSerialize class with alias."""

    def setup(self, *args, **kwargs):
        r"""Create an instance of the class."""
        super(TestDefaultSerialize_alias, self).setup(*args, **kwargs)
        alias = self.instance
        self._instance = DefaultSerialize.DefaultSerialize()
        self._instance._alias = alias


class TestDefaultSerialize_type(TestDefaultSerialize):
    r"""Test class for DefaultSerialize class with types."""

    def get_options(self):
        r"""Get testing options."""
        out = {'kwargs': {'type': 'float'},
               'empty': b'',
               'objects': [float(x) for x in range(5)],
               'extra_kwargs': {},
               'typedef': {'type': 'float'},
               'dtype': None}
        return out


class TestDefaultSerialize_func_error(TestDefaultSerialize_func):
    r"""Test class for DefaultSerialize class with incorrect functions."""

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
