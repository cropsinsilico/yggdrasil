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

    def test_deserialize_no_header(self):
        r"""Test deserialization of frame output without a header."""
        if self.testing_option_kws.get('no_header', False):
            return
        kws = self.instance.get_testing_options(no_header=True)
        kws['kwargs'].pop('no_header', None)
        no_head_inst = self.import_cls(**kws['kwargs'])
        x = no_head_inst.serialize(kws['objects'][0])
        y = self.instance.deserialize(x)[0]
        self.assert_result_equal(y, self.testing_options['objects'][0])


class TestPandasSerializeNoHeader(TestPandasSerialize):
    r"""Test class for PandasSerialize class when no header specified."""

    testing_option_kws = {'no_header': True}

    
class TestPandasSerializeBytes(TestPandasSerialize):
    r"""Test class for PandasSerialize class when strings are bytes."""

    testing_option_kws = {'table_string_type': 'bytes'}
