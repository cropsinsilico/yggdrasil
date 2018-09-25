import numpy as np
import nose.tools as nt
from cis_interface import backwards
from cis_interface.serialize import AsciiTableSerialize
from cis_interface.serialize.tests.test_DefaultSerialize import \
    TestDefaultSerialize


def test_serialize_nofmt():
    r"""Test error on serialization without a format."""
    inst = AsciiTableSerialize.AsciiTableSerialize()
    test_msg = np.zeros((5, 5))
    nt.assert_raises(RuntimeError, inst.serialize, test_msg)
    nt.assert_equal(inst.table_info, None)

    
def test_deserialize_nofmt():
    r"""Test error on deserialization without a format."""
    inst = AsciiTableSerialize.AsciiTableSerialize()
    test_msg = backwards.unicode2bytes('lskdbjs;kfbj')
    nt.assert_raises(RuntimeError, inst.deserialize, test_msg)


class TestAsciiTableSerialize(TestDefaultSerialize):
    r"""Test class for AsciiTableSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestAsciiTableSerialize, self).__init__(*args, **kwargs)
        self._cls = 'AsciiTableSerialize'
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
        self.instance.table_info


class TestAsciiTableSerializeSingle(TestDefaultSerialize):
    r"""Test class for AsciiTableSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestAsciiTableSerializeSingle, self).__init__(*args, **kwargs)
        self._inst_kwargs['format_str'] = backwards.unicode2bytes('%d\n')
        self._cls = 'AsciiTableSerialize'
        self._empty_obj = tuple()
        self._objects = [(1, )]

    def test_field_specs(self):
        r"""Test field specifiers."""
        nt.assert_equal(self.instance.format_str, self._inst_kwargs['format_str'])
        nt.assert_equal(self.instance.nfields, 1)
        nt.assert_equal(self.instance.field_names, None)
        nt.assert_equal(self.instance.field_units, None)
        fmt_list = [backwards.unicode2bytes('%d')]
        nt.assert_equal(self.instance.field_formats, fmt_list)


class TestAsciiTableSerialize_asarray(TestAsciiTableSerialize):
    r"""Test class for AsciiTableSerialize class with as_array."""

    def __init__(self, *args, **kwargs):
        super(TestAsciiTableSerialize_asarray, self).__init__(*args, **kwargs)
        self._inst_kwargs['as_array'] = True
        self._objects = [self.file_array]

    def assert_result_equal(self, x, y):
        r"""Assert that serialized/deserialized objects equal."""
        np.testing.assert_array_equal(x, y)
