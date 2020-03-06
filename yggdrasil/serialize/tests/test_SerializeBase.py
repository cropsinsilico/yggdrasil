import copy
from yggdrasil.tests import YggTestClassInfo, assert_equal
from yggdrasil import tools
from yggdrasil.components import import_component
from yggdrasil.serialize import SerializeBase


def test_demote_string():
    r"""Test format str creation of typedef."""
    x = SerializeBase.SerializeBase(format_str='%s')
    assert_equal(x.typedef, {'type': 'array',
                             'items': [{'type': 'bytes'}]})


class TestSerializeBase(YggTestClassInfo):
    r"""Test class for SerializeBase class."""

    _cls = 'SerializeBase'
    _empty_msg = b''
    attr_list = (copy.deepcopy(YggTestClassInfo.attr_list)
                 + ['datatype', 'typedef', 'numpy_dtype'])

    def __init__(self, *args, **kwargs):
        super(TestSerializeBase, self).__init__(*args, **kwargs)
        self._header_info = dict(arg1='1', arg2='two')

    @property
    def mod(self):
        r"""Module for class to be tested."""
        return 'yggdrasil.serialize.%s' % self.cls

    @property
    def inst_kwargs(self):
        r"""Keyword arguments for creating the test instance."""
        out = super(TestSerializeBase, self).inst_kwargs
        out.update(self.testing_options['kwargs'])
        return out

    def empty_head(self, msg):
        r"""dict: Empty header for message only contains the size."""
        out = dict(size=len(msg), incomplete=False)
        if msg == tools.YGG_MSG_EOF:  # pragma: debug
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

    def test_concatenation(self):
        r"""Test message concatenation."""
        for x, y in self.testing_options.get('concatenate', []):
            self.assert_equal(self.instance.concatenate(x), y)
        
    def test_serialize(self):
        r"""Test serialize/deserialize."""
        for iobj in self.testing_options['objects']:
            if (self._cls == 'SerializeBase'):
                self.assert_raises(NotImplementedError, self.instance.serialize, iobj)
                self.assert_raises(NotImplementedError, self.instance.deserialize,
                                   b'test')
                break
            msg = self.instance.serialize(iobj)
            iout, ihead = self.instance.deserialize(msg)
            self.assert_result_equal(iout, iobj)
            # self.assert_equal(ihead, self.empty_head(msg))

    def test_serialize_no_metadata(self):
        r"""Test serializing without metadata."""
        if (self._cls == 'SerializeBase'):
            return
        self.instance.serialize(self.testing_options['objects'][0],
                                no_metadata=True)

    def test_deserialize_error(self):
        r"""Test error when deserializing message that is not bytes."""
        self.assert_raises(TypeError, self.instance.deserialize, None)
        
    def test_serialize_sinfo(self):
        r"""Test serialize/deserialize with serializer info."""
        if (self._cls == 'SerializeBase'):
            return
        hout = copy.deepcopy(self._header_info)
        temp_seri = import_component(
            'serializer', self.instance.serializer_info['seritype'])()
        for iobj in self.testing_options['objects']:
            msg = self.instance.serialize(iobj, header_kwargs=self._header_info,
                                          add_serializer_info=True)
            hout.update(self.instance.serializer_info)
            hout.update(self.instance.datatype.encode_type(
                iobj, typedef=self.instance.typedef))
            iout, ihead = self.instance.deserialize(msg)
            hout.update(size=ihead['size'], id=ihead['id'],
                        incomplete=False)
            self.assert_result_equal(iout, iobj)
            self.assert_equal(ihead, hout)
            # Use info to reconstruct serializer
            iout, ihead = temp_seri.deserialize(msg)
            self.assert_result_equal(iout, iobj)
            self.assert_equal(ihead, hout)
            new_seri = import_component('serializer',
                                        ihead.pop('seritype', None))(**ihead)
            iout, ihead = new_seri.deserialize(msg)
            self.assert_result_equal(iout, iobj)
            self.assert_equal(ihead, hout)
            
    def test_serialize_header(self):
        r"""Test serialize/deserialize with header."""
        if (self._cls == 'SerializeBase'):
            return
        for iobj in self.testing_options['objects']:
            msg = self.instance.serialize(iobj, header_kwargs=self._header_info)
            iout, ihead = self.instance.deserialize(msg)
            self.assert_result_equal(iout, iobj)
            # self.assert_equal(ihead, self._header_info)
        
    def test_serialize_eof(self):
        r"""Test serialize/deserialize EOF."""
        if (self._cls == 'SerializeBase'):
            return
        iobj = tools.YGG_MSG_EOF
        msg = self.instance.serialize(iobj)
        iout, ihead = self.instance.deserialize(msg)
        self.assert_equal(iout, iobj)
        # self.assert_equal(ihead, self.empty_head(msg))
        
    def test_serialize_eof_header(self):
        r"""Test serialize/deserialize EOF with header."""
        if (self._cls == 'SerializeBase'):
            return
        iobj = tools.YGG_MSG_EOF
        msg = self.instance.serialize(iobj, header_kwargs=self._header_info)
        iout, ihead = self.instance.deserialize(msg)
        self.assert_equal(iout, iobj)
        # self.assert_equal(ihead, self.empty_head(msg))
        
    def test_deserialize_empty(self):
        r"""Test call for empty string."""
        if (self._cls == 'SerializeBase'):
            return
        out, head = self.instance.deserialize(self._empty_msg)
        self.assert_result_equal(out, self.testing_options['empty'])
        self.assert_equal(head, self.empty_head(self._empty_msg))
