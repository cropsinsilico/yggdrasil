import nose.tools as nt
from cis_interface import backwards
from cis_interface.tests import CisTest, IOInfo


class TestDefaultDeserialize(CisTest, IOInfo):
    r"""Test class for DefaultDeserialize class."""

    def __init__(self, *args, **kwargs):
        super(TestDefaultDeserialize, self).__init__(*args, **kwargs)
        IOInfo.__init__(self)
        self._cls = 'DefaultDeserialize'
        self._result_empty = backwards.unicode2bytes('')

    @property
    def mod(self):
        r"""Module for class to be tested."""
        return 'cis_interface.serialize.%s' % self.cls

    def test_call(self):
        r"""Test call without format string."""
        for iline in self.file_lines:
            iout = self.instance(iline)
            nt.assert_equal(iout, iline)

    def test_call_empty(self):
        r"""Test call for empty string."""
        test_msg = backwards.unicode2bytes('')
        out = self.instance(test_msg)
        nt.assert_equal(out, self._result_empty)


class TestDefaultDeserialize_format(TestDefaultDeserialize):
    r"""Test class for DefaultDeserialize class with format."""

    def __init__(self, *args, **kwargs):
        super(TestDefaultDeserialize_format, self).__init__(*args, **kwargs)
        self._inst_kwargs = {'format_str': self.fmt_str}
        self._result_empty = tuple()

    def test_call(self):
        r"""Test call with format string."""
        for iargs, iline in zip(self.file_rows, self.file_lines):
            iout = self.instance(iline)
            nt.assert_equal(iout, iargs)
