import numpy as np
import nose.tools as nt
from cis_interface.tests import CisTestClassInfo
from cis_interface import backwards, tools, serialize
from cis_interface.serialize import DefaultSerialize


class TestDefaultSerialize(CisTestClassInfo):
    r"""Test class for DefaultSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestDefaultSerialize, self).__init__(*args, **kwargs)
        self._cls = 'DefaultSerialize'
        self._empty_msg = backwards.unicode2bytes('')
        self._empty_obj = backwards.unicode2bytes('')
        self._header_info = dict(arg1='1', arg2='two')
        self._objects = self.file_lines
        self.attr_list += ['format_str', 'as_array', 'field_names',
                           'field_units', 'nfields', 'field_formats',
                           'numpy_dtype', 'scanf_format_str', 'serializer_info']

    def map_sent2recv(self, obj):
        r"""Convert a sent object into a received one."""
        return obj

    @property
    def mod(self):
        r"""Module for class to be tested."""
        return 'cis_interface.serialize.%s' % self.cls

    def empty_head(self, msg):
        r"""dict: Empty header for message only contains the size."""
        out = dict(size=len(msg))
        if msg == tools.CIS_MSG_EOF:
            out['eof'] = True
        return out

    def assert_result_equal(self, x, y):
        r"""Assert that serialized/deserialized objects equal."""
        nt.assert_equal(x, y)

    def test_field_specs(self):
        r"""Test field specifiers."""
        nt.assert_equal(self.instance.format_str, None)
        nt.assert_equal(self.instance.nfields, 0)
        nt.assert_equal(self.instance.field_names, None)
        nt.assert_equal(self.instance.field_units, None)
        nt.assert_equal(self.instance.field_formats, [])
        nt.assert_equal(self.instance.numpy_dtype, None)
        nt.assert_equal(self.instance.scanf_format_str, None)
        nt.assert_equal(self.instance.is_user_defined, False)
        
    def test_serialize(self):
        r"""Test serialize/deserialize."""
        for iobj in self._objects:
            msg = self.instance.serialize(iobj)
            iout, ihead = self.instance.deserialize(msg)
            self.assert_result_equal(iout, self.map_sent2recv(iobj))
            nt.assert_equal(ihead, self.empty_head(msg))

    def test_deserialize_error(self):
        r"""Test error when deserializing message that is not bytes."""
        nt.assert_raises(TypeError, self.instance.deserialize, None)
        
    def test_serialize_sinfo(self):
        r"""Test serialize/deserialize with serializer info."""
        hout = self._header_info
        hout.update(**self.instance.serializer_info)
        temp_seri = serialize.get_serializer(
            stype=self.instance.serializer_info['stype'])
        for iobj in self._objects:
            msg = self.instance.serialize(iobj, header_kwargs=self._header_info,
                                          add_serializer_info=True)
            iout, ihead = self.instance.deserialize(msg)
            self.assert_result_equal(iout, self.map_sent2recv(iobj))
            nt.assert_equal(ihead, hout)
            # Use info to reconstruct serializer
            iout, ihead = temp_seri.deserialize(msg)
            self.assert_result_equal(iout, self.map_sent2recv(iobj))
            nt.assert_equal(ihead, hout)
            new_seri = serialize.get_serializer(**ihead)
            iout, ihead = new_seri.deserialize(msg)
            self.assert_result_equal(iout, self.map_sent2recv(iobj))
            nt.assert_equal(ihead, hout)
        
    def test_serialize_header(self):
        r"""Test serialize/deserialize with header."""
        for iobj in self._objects:
            msg = self.instance.serialize(iobj, header_kwargs=self._header_info)
            iout, ihead = self.instance.deserialize(msg)
            self.assert_result_equal(iout, self.map_sent2recv(iobj))
            nt.assert_equal(ihead, self._header_info)
        
    def test_serialize_eof(self):
        r"""Test serialize/deserialize EOF."""
        iobj = tools.CIS_MSG_EOF
        msg = self.instance.serialize(iobj)
        iout, ihead = self.instance.deserialize(msg)
        nt.assert_equal(iout, iobj)
        nt.assert_equal(ihead, self.empty_head(msg))
        
    def test_serialize_eof_header(self):
        r"""Test serialize/deserialize EOF with header."""
        iobj = tools.CIS_MSG_EOF
        msg = self.instance.serialize(iobj, header_kwargs=self._header_info)
        iout, ihead = self.instance.deserialize(msg)
        nt.assert_equal(iout, iobj)
        nt.assert_equal(ihead, self.empty_head(msg))
        
    def test_serialize_no_format(self):
        r"""Test serialize/deserialize without format string."""
        if (len(self._inst_kwargs) == 0) and (self._cls == 'DefaultSerialize'):
            for iobj in self._objects:
                msg = self.instance.serialize([iobj],
                                              header_kwargs=self._header_info)
                iout, ihead = self.instance.deserialize(msg)
                self.assert_result_equal(iout, self.map_sent2recv(iobj))
                nt.assert_equal(ihead, self._header_info)
            nt.assert_raises(Exception, self.instance.serialize, ['msg', 0])
        
    def test_deserialize_empty(self):
        r"""Test call for empty string."""
        out, head = self.instance.deserialize(self._empty_msg)
        nt.assert_equal(out, self._empty_obj)
        nt.assert_equal(head, self.empty_head(self._empty_msg))


class TestDefaultSerialize_format(TestDefaultSerialize):
    r"""Test class for DefaultSerialize class with format."""

    def __init__(self, *args, **kwargs):
        super(TestDefaultSerialize_format, self).__init__(*args, **kwargs)
        self._inst_kwargs = {'format_str': self.fmt_str,
                             'field_names': self.field_names,
                             'field_units': self.field_units}
        self._empty_obj = tuple()
        self._objects = self.file_rows

    def test_field_specs(self):
        r"""Test field specifiers."""
        nt.assert_equal(self.instance.format_str, self.fmt_str)
        nt.assert_equal(self.instance.nfields, self.nfields)
        nt.assert_equal(self.instance.field_names, self.field_names)
        nt.assert_equal(self.instance.field_units, self.field_units)
        nt.assert_equal(self.instance.field_formats, self.field_formats)
        nt.assert_equal(self.instance.numpy_dtype, self.file_dtype)
        scanf_fmt = backwards.unicode2bytes('%s\t%d\t%f\n')
        nt.assert_equal(self.instance.scanf_format_str, scanf_fmt)


class TestDefaultSerialize_array(TestDefaultSerialize_format):
    r"""Test class for DefaultSerialize class with format as array."""

    def __init__(self, *args, **kwargs):
        super(TestDefaultSerialize_array, self).__init__(*args, **kwargs)
        self._inst_kwargs['as_array'] = True
        self._empty_obj = tuple()
        self._objects = [self.file_array]

    def assert_result_equal(self, x, y):
        r"""Assert that serialized/deserialized objects equal."""
        np.testing.assert_array_equal(x, y)


class TestDefaultSerialize_func(TestDefaultSerialize):
    r"""Test class for DefaultSerialize class with functions."""

    def __init__(self, *args, **kwargs):
        super(TestDefaultSerialize_func, self).__init__(*args, **kwargs)
        self.func_serialize = self._func_serialize
        self.func_deserialize = self._func_deserialize
        self._inst_kwargs = {'func_serialize': self.func_serialize,
                             'func_deserialize': self.func_deserialize}
        self._objects = self.file_rows

    def _func_serialize(self, args):
        r"""Method that serializes using repr."""
        return backwards.unicode2bytes(repr(args))

    def _func_deserialize(self, args):
        r"""Method that deserializes using eval."""
        if len(args) == 0:
            return self._empty_obj
        x = eval(backwards.bytes2unicode(args))
        return x

    def test_field_specs(self):
        r"""Test field specifiers."""
        nt.assert_equal(self.instance.format_str, None)
        nt.assert_equal(self.instance.nfields, 0)
        nt.assert_equal(self.instance.field_names, None)
        nt.assert_equal(self.instance.field_units, None)
        nt.assert_equal(self.instance.field_formats, [])
        nt.assert_equal(self.instance.numpy_dtype, None)
        nt.assert_equal(self.instance.scanf_format_str, None)
        nt.assert_equal(self.instance.is_user_defined, True)
        nt.assert_equal(self.instance.serializer_type, -1)
        
    def test_serialize_sinfo(self):
        r"""Test error on serialize with serializer info for function."""
        nt.assert_raises(RuntimeError, self.instance.serialize,
                         self._objects[0], add_serializer_info=True)


class TestDefaultSerialize_class(TestDefaultSerialize_func):
    r"""Test class for DefaultSerialize class with classes."""

    def __init__(self, *args, **kwargs):
        super(TestDefaultSerialize_class, self).__init__(*args, **kwargs)
        temp_seri = DefaultSerialize.DefaultSerialize(format_str=self.fmt_str)
        self._empty_obj = tuple()
        self.func_serialize = temp_seri
        self.func_deserialize = temp_seri
        self._inst_kwargs = {'func_serialize': self.func_serialize,
                             'func_deserialize': self.func_deserialize}


class TestDefaultSerialize_alias(TestDefaultSerialize_format):
    r"""Test class for DefaultSerialize class with alias."""

    def setup(self, *args, **kwargs):
        r"""Create an instance of the class."""
        super(TestDefaultSerialize_alias, self).setup(*args, **kwargs)
        alias = self.instance
        self._instance = DefaultSerialize.DefaultSerialize()
        self._instance._alias = alias


class TestDefaultSerialize_func_error(TestDefaultSerialize_func):
    r"""Test class for DefaultSerialize class with incorrect functions."""

    def _func_serialize(self, args):
        r"""Method that serializes using repr."""
        return args

    def test_serialize(self):
        r"""Test serialize with function that dosn't return correct type."""
        nt.assert_raises(TypeError, self.instance.serialize, (1,))

    def test_serialize_header(self):
        r"""Disabled: Test serialize/deserialize with header."""
        pass

    def test_serialize_sinfo(self):
        r"""Disabled: Test serialize/deserialize with serializer info."""
        pass

    def test_field_specs(self):
        r"""Disabled: Test field specifiers."""
        pass
