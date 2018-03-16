import nose.tools as nt
from cis_interface.tests import CisTestClassInfo
from cis_interface import backwards


class TestDefaultSerialize(CisTestClassInfo):
    r"""Test class for DefaultSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestDefaultSerialize, self).__init__(*args, **kwargs)
        self._cls = 'DefaultSerialize'
        self._empty_msg = backwards.unicode2bytes('')
        self._empty_obj = backwards.unicode2bytes('')

    @property
    def mod(self):
        r"""Module for class to be tested."""
        return 'cis_interface.serialize.%s' % self.cls

    def test_serialize(self):
        r"""Test serialize without format string."""
        for iline in self.file_lines:
            iout = self.instance.serialize(iline)
            nt.assert_equal(iout, iline)
            iout = self.instance.serialize([iline])
            nt.assert_equal(iout, iline)
        nt.assert_raises(Exception, self.instance.serialize, ['msg', 0])
        
    def test_deserialize(self):
        r"""Test deserialize without format string."""
        for iline in self.file_lines:
            iout = self.instance.deserialize(iline)
            nt.assert_equal(iout, iline)

    def test_deserialize_empty(self):
        r"""Test call for empty string."""
        out = self.instance.deserialize(self._empty_msg)
        nt.assert_equal(out, self._empty_obj)


class TestDefaultSerialize_format(TestDefaultSerialize):
    r"""Test class for DefaultSerialize class with format."""

    def __init__(self, *args, **kwargs):
        super(TestDefaultSerialize_format, self).__init__(*args, **kwargs)
        self._inst_kwargs = {'format_str': self.fmt_str}
        self._empty_obj = tuple()

    def test_serialize(self):
        r"""Test serialize with format string."""
        for iargs, iline in zip(self.file_rows, self.file_lines):
            iout = self.instance.serialize(iargs)
            nt.assert_equal(iout, iline)

    def test_deserialize(self):
        r"""Test deserialize with format string."""
        for iargs, iline in zip(self.file_rows, self.file_lines):
            iout = self.instance.deserialize(iline)
            nt.assert_equal(iout, iargs)


class TestDefaultSerialize_func(TestDefaultSerialize):
    r"""Test class for DefaultSerialize class with functions."""

    def __init__(self, *args, **kwargs):
        super(TestDefaultSerialize_func, self).__init__(*args, **kwargs)
        self._inst_kwargs = {'func_serialize': self.func_serialize,
                             'func_deserialize': self.func_deserialize}

    def func_serialize(self, args):
        r"""Method that serializes using repr."""
        return backwards.unicode2bytes(repr(args))

    def func_deserialize(self, args):
        r"""Method that deserializes using eval."""
        x = eval(backwards.bytes2unicode(args))
        return x

    def test_serialize(self):
        r"""Test serialize with function."""
        for iargs in self.file_rows:
            iout = self.instance.serialize(iargs)
            nt.assert_equal(iout, self.func_serialize(iargs))

    def test_deserialize(self):
        r"""Test deserialize with function."""
        for iargs in self.file_rows:
            iout = self.instance.deserialize(self.func_serialize(iargs))
            nt.assert_equal(iout, iargs)


class TestDefaultSerialize_func_error(TestDefaultSerialize_func):
    r"""Test class for DefaultSerialize class with incorrect functions."""

    def func_serialize(self, args):
        r"""Method that serializes using repr."""
        return args

    def func_deserialize(self, args):
        r"""Method that deserializes using eval."""
        x = eval(backwards.bytes2unicode(args))
        return x

    def test_serialize(self):
        r"""Test serialize with function."""
        nt.assert_raises(TypeError, self.instance.serialize, (1,))

    def test_deserialize(self):
        r"""Test deserialize with function."""
        nt.assert_raises(TypeError, self.instance.deserialize, (1,))
