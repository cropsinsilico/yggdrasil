import numpy as np
import nose.tools as nt
from cis_interface.serialize.tests.test_DefaultDeserialize import \
    TestDefaultDeserialize


class TestAsciiTableDeserialize(TestDefaultDeserialize):
    r"""Test class for AsciiTableDeserialize class."""

    def __init__(self, *args, **kwargs):
        super(TestAsciiTableDeserialize, self).__init__(*args, **kwargs)
        self._cls = 'AsciiTableDeserialize'
        self._inst_kwargs = {'format_str': self.fmt_str}
        self._result_empty = tuple()

    def test_call(self):
        r"""Test call as rows."""
        for iline, iargs in zip(self.file_lines, self.file_rows):
            iout = self.instance(iline)
            nt.assert_equal(iout, iargs)


class TestAsciiTableDeserialize_asarray(TestAsciiTableDeserialize):
    r"""Test class for AsciiTableDeserialize class with as_array."""

    def __init__(self, *args, **kwargs):
        super(TestAsciiTableDeserialize_asarray, self).__init__(*args, **kwargs)
        self._inst_kwargs['as_array'] = True

    def test_call(self):
        r"""Test call as array."""
        iout = self.instance(self.file_bytes)
        np.testing.assert_array_equal(iout, self.file_array)
