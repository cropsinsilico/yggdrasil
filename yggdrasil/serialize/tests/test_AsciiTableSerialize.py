import copy
import numpy as np
from yggdrasil import backwards
from yggdrasil.tests import assert_raises
from yggdrasil.serialize import AsciiTableSerialize
from yggdrasil.serialize.tests import test_DefaultSerialize as parent


def test_serialize_nofmt():
    r"""Test error on serialization without a format."""
    inst = AsciiTableSerialize.AsciiTableSerialize()
    inst._initialized = True
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
        super(TestAsciiTableSerialize, self).test_field_specs()
        # Specific to this class
        self.assert_equal(self.instance.format_str,
                          backwards.as_bytes(
                              self.testing_options['kwargs']['format_str']))
        field_names = self.testing_options['kwargs'].get('field_names', None)
        if field_names is not None:
            field_names = [backwards.as_str(x) for x in field_names]
        self.assert_equal(self.instance.field_names, field_names)
        field_units = self.testing_options['kwargs'].get('field_units', None)
        if field_units is not None:
            field_units = [backwards.as_str(x) for x in field_units]
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
