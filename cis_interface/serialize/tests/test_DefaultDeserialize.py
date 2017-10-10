import nose.tools as nt
from cis_interface.tests import CisTest
from cis_interface.drivers.tests.test_IODriver import IOInfo


class TestDefaultDeserialize(CisTest, IOInfo):
    r"""Test class for DefaultDeserialize class."""

    def __init__(self, *args, **kwargs):
        super(TestDefaultDeserialize, self).__init__(*args, **kwargs)
        IOInfo.__init__(self)
        self._cls = 'DefaultDeserialize'

    @property
    def mod(self):
        r"""Module for class to be tested."""
        return 'cis_interface.serialize.%s' % self.cls

    def test_call(self):
        r"""Test call without format string."""
        for iline in self.file_lines:
            iout = self.instance(iline)
            nt.assert_equal(iout, iline)


class TestDefaultDeserialize_format(TestDefaultDeserialize):
    r"""Test class for DefaultDeserialize class with format."""

    def __init__(self, *args, **kwargs):
        super(TestDefaultDeserialize_format, self).__init__(*args, **kwargs)
        self._inst_kwargs = {'format_str': self.fmt_str}

    def test_call(self):
        r"""Test call with format string."""
        for iargs, iline in zip(self.file_rows, self.file_lines):
            iout = self.instance(iline)
            nt.assert_equal(iout, iargs)
