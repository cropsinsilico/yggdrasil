import nose.tools as nt
import numpy as np
from cis_interface import backwards
from cis_interface.serialize.tests.test_DefaultSerialize import \
    TestDefaultSerialize


class TestAsciiTableSerialize(TestDefaultSerialize):
    r"""Test class for AsciiTableSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestAsciiTableSerialize, self).__init__(*args, **kwargs)
        self._cls = 'AsciiTableSerialize'
        self._inst_kwargs = {'format_str': self.fmt_str}
        self._empty_obj = tuple()

    def test_serialize(self):
        r"""Test serialize as rows."""
        for iline, iargs in zip(self.file_lines, self.file_rows):
            iout = self.instance.serialize(iargs)
            nt.assert_equal(iout, iline)

    def test_deserialize(self):
        r"""Test deserialize as rows."""
        for iline, iargs in zip(self.file_lines, self.file_rows):
            iout = self.instance.deserialize(iline)
            nt.assert_equal(iout, iargs)


class TestAsciiTableSerializeSingle(TestAsciiTableSerialize):
    r"""Test class for AsciiTableSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestAsciiTableSerializeSingle, self).__init__(*args, **kwargs)
        self._inst_kwargs['format_str'] = '%d'

    def test_serialize(self):
        r"""Test serialize for single element."""
        nt.assert_equal(self.instance.serialize(1), backwards.unicode2bytes('1'))

    def test_deserialize(self):
        r"""Test deserialize for single element."""
        nt.assert_equal(self.instance.deserialize(backwards.unicode2bytes('1\n')), (1,))
        

class TestAsciiTableSerialize_asarray(TestAsciiTableSerialize):
    r"""Test class for AsciiTableSerialize class with as_array."""

    def __init__(self, *args, **kwargs):
        super(TestAsciiTableSerialize_asarray, self).__init__(*args, **kwargs)
        self._inst_kwargs['as_array'] = True

    def test_serialize(self):
        r"""Test serialize as array."""
        iout = self.instance.serialize(self.file_array)
        nt.assert_equal(iout, self.file_bytes)

    def test_deserialize(self):
        r"""Test deserialize as array."""
        iout = self.instance.deserialize(self.file_bytes)
        np.testing.assert_array_equal(iout, self.file_array)
