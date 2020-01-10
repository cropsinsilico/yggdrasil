from yggdrasil.serialize.tests import test_AsciiTableSerialize as parent


class TestPandasSerialize(parent.TestAsciiTableSerialize):
    r"""Test class for TestPandasSerialize class."""

    _cls = 'PandasSerialize'

    def test_apply_field_names_errors(self):
        r"""Test errors raised by apply_field_names."""
        self.assert_raises(RuntimeError, self.instance.apply_field_names,
                           self.testing_options['objects'][0],
                           field_names=['x', 'y'])
        names = self.testing_options['objects'][0].columns.tolist()
        names[0] = 'invalid'
        self.assert_raises(RuntimeError, self.instance.apply_field_names,
                           self.testing_options['objects'][0],
                           field_names=names)

    def test_func_serialize_errors(self):
        r"""Test errors raised by func_serialize."""
        self.assert_raises(TypeError, self.instance.func_serialize, None)


class TestPandasSerializeNoHeader(TestPandasSerialize):
    r"""Test class for PandasSerialize class when no header specified."""

    testing_option_kws = {'no_header': True}
