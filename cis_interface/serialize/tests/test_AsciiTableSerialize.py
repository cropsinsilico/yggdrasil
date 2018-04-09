import numpy as np
from cis_interface.serialize.tests.test_DefaultSerialize import \
    TestDefaultSerialize


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


class TestAsciiTableSerializeSingle(TestAsciiTableSerialize):
    r"""Test class for AsciiTableSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestAsciiTableSerializeSingle, self).__init__(*args, **kwargs)
        self._inst_kwargs['format_str'] = '%d\n'
        self._objects = [(1, )]


class TestAsciiTableSerialize_asarray(TestAsciiTableSerialize):
    r"""Test class for AsciiTableSerialize class with as_array."""

    def __init__(self, *args, **kwargs):
        super(TestAsciiTableSerialize_asarray, self).__init__(*args, **kwargs)
        self._inst_kwargs['as_array'] = True
        self._objects = [self.file_array]

    def assert_result_equal(self, x, y):
        r"""Assert that serialized/deserialized objects equal."""
        np.testing.assert_array_equal(x, y)
