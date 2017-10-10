import nose.tools as nt
from cis_interface.tests import CisTest
from cis_interface.drivers.tests.test_IODriver import IOInfo


class TestDefaultSerialize(CisTest, IOInfo):
    r"""Test class for DefaultSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestDefaultSerialize, self).__init__(*args, **kwargs)
        IOInfo.__init__(self)
        self._cls = 'DefaultSerialize'

    @property
    def mod(self):
        r"""Module for class to be tested."""
        return 'cis_interface.serialize.%s' % self.cls

    def test_call(self):
        r"""Test call without format string."""
        for iline in self.file_lines:
            iout = self.instance(iline)
            nt.assert_equal(iout, iline)
            iout = self.instance([iline])
            nt.assert_equal(iout, iline)
        nt.assert_raises(Exception, self.instance, ['msg', 0])


class TestDefaultSerialize_format(TestDefaultSerialize):
    r"""Test class for DefaultSerialize class with format."""

    def __init__(self, *args, **kwargs):
        super(TestDefaultSerialize_format, self).__init__(*args, **kwargs)
        self._inst_kwargs = {'format_str': self.fmt_str}

    def test_call(self):
        r"""Test call with format string."""
        for iargs, iline in zip(self.file_rows, self.file_lines):
            iout = self.instance(iargs)
            nt.assert_equal(iout, iline)
