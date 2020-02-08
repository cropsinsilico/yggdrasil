import copy
import numpy as np
from yggdrasil.tests import assert_raises
from yggdrasil.serialize import AsciiTableSerialize
from yggdrasil.serialize.tests import test_DefaultSerialize as parent


def test_serialize_nofmt():
    r"""Test error on serialization without a format."""
    inst = AsciiTableSerialize.AsciiTableSerialize()
    inst.initialized = True
    test_msg = np.zeros((5, 5))
    assert_raises(RuntimeError, inst.serialize, test_msg)

    
def test_deserialize_nofmt():
    r"""Test error on deserialization without a format."""
    inst = AsciiTableSerialize.AsciiTableSerialize()
    test_msg = b'lskdbjs;kfbj'
    test_msg = inst.encoded_datatype.serialize(test_msg, metadata={})
    assert_raises(RuntimeError, inst.deserialize, test_msg)


class TestAsciiTableSerialize(parent.TestDefaultSerialize):
    r"""Test class for AsciiTableSerialize class."""

    _cls = 'AsciiTableSerialize'
    attr_list = (copy.deepcopy(parent.TestDefaultSerialize.attr_list),
                 ['format_str', 'field_names', 'field_units', 'as_array'])
    
    def test_field_specs(self):
        r"""Test field specifiers."""
        if not self.instance.initialized:
            self.instance.serialize(self.testing_options['objects'][0],
                                    no_metadata=True)
        super(TestAsciiTableSerialize, self).test_field_specs()
        # Specific to this class
        if 'format_str' in self.testing_options:
            self.assert_equal(self.instance.format_str,
                              self.testing_options['format_str'].encode("utf-8"))
        field_names = self.testing_options.get('field_names', None)
        self.assert_equal(self.instance.field_names, field_names)
        field_units = self.testing_options.get('field_units', None)
        self.assert_equal(self.instance.field_units, field_units)


class TestAsciiTableSerializeSingle(parent.TestDefaultSerialize):
    r"""Test class for AsciiTableSerialize class."""

    _cls = 'AsciiTableSerialize'
    _empty_obj = []
    _objects = [(1, )]

    def __init__(self, *args, **kwargs):
        super(TestAsciiTableSerializeSingle, self).__init__(*args, **kwargs)
        self._inst_kwargs['format_str'] = '%d\n'

    def get_options(self):
        r"""Get testing options."""
        out = {'kwargs': {'format_str': '%d\n'},
               'empty': [],
               'objects': [(1, )],
               'extra_kwargs': {},
               'typedef': {'type': 'array',
                           'items': [{'type': 'int', 'precision': 32}]},
               'dtype': None,
               'is_user_defined': False}
        return out


class TestAsciiTableSerialize_asarray(TestAsciiTableSerialize):
    r"""Test class for AsciiTableSerialize class with as_array."""

    testing_option_kws = {'array_columns': True}


class TestAsciiTableSerialize_object(TestAsciiTableSerialize):
    r"""Test class for AsciiTableSerialize class with object."""

    testing_option_kws = {}

    def get_options(self):
        r"""Get testing options."""
        out = super(TestAsciiTableSerialize_object, self).get_options()
        out['kwargs'] = {'field_units': out['kwargs']['field_units']}
        out['format_str'] = '%s\t%d\t%g\n'
        out['field_names'] = ['%s_%s' % (k, x) for k, x
                              in zip('abc', out['field_names'])]
        out['objects'] = [{k: ix for k, ix in zip(out['field_names'], x)}
                          for x in out['objects']]
        for x, k2 in zip(out['typedef']['items'], out['field_names']):
            out['contents'].replace(x['title'].encode("utf-8"),
                                    k2.encode("utf-8"))
            x['title'] = k2
        return out

    def map_sent2recv(self, obj):
        r"""Convert a sent object into a received one."""
        out = super(TestAsciiTableSerialize_object, self).map_sent2recv(obj)
        return self.instance.datatype.coerce_type(
            out, typedef=self.instance.typedef)
