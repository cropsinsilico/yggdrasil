import nose.tools as nt
from cis_interface import backwards
from cis_interface.serialize.tests.test_DefaultSerialize import \
    TestDefaultSerialize


class TestAsciiTableSerialize(TestDefaultSerialize):
    r"""Test class for AsciiTableSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestAsciiTableSerialize, self).__init__(*args, **kwargs)
        self._cls = 'AsciiTableSerialize'
        self._inst_kwargs = {'format_str': self.fmt_str}

    def test_call(self):
        r"""Test call as rows."""
        for iline, iargs in zip(self.file_lines, self.file_rows):
            iout = self.instance(iargs)
            nt.assert_equal(iout, iline)


class TestAsciiTableSerializeSingle(TestAsciiTableSerialize):
    r"""Test class for AsciiTableSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestAsciiTableSerializeSingle, self).__init__(*args, **kwargs)
        self._inst_kwargs['format_str'] = '%d'

    def test_call(self):
        r"""Test call for single element."""
        nt.assert_equal(self.instance(1), backwards.unicode2bytes('1'))


class TestAsciiTableSerialize_asarray(TestAsciiTableSerialize):
    r"""Test class for AsciiTableSerialize class with as_array."""

    def __init__(self, *args, **kwargs):
        super(TestAsciiTableSerialize_asarray, self).__init__(*args, **kwargs)
        self._inst_kwargs['as_array'] = True

    def test_call(self):
        r"""Test call as array."""
        iout = self.instance(self.file_array)
        nt.assert_equal(iout, self.file_bytes)
