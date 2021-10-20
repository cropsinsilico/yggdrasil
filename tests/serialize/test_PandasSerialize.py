import pytest
from tests.serialize.test_AsciiTableSerialize import (
    TestAsciiTableSerialize as base_class)


@pytest.mark.usefixtures("pandas_equality_patch")
class TestPandasSerialize(base_class):
    r"""Test class for TestPandasSerialize class."""

    @pytest.fixture(scope="class", autouse=True)
    def serializer(self):
        r"""str: Serializer being tested."""
        return "pandas"

    @pytest.fixture(scope="class", autouse=True,
                    params=[{}, {'no_header': True},
                            {'table_string_type': 'bytes'}])
    def options(self, request):
        r"""Arguments that should be provided when getting testing options."""
        return request.param

    def test_apply_field_names_errors(self, instance, testing_options):
        r"""Test errors raised by apply_field_names."""
        with pytest.raises(RuntimeError):
            instance.apply_field_names(testing_options['objects'][0],
                                       field_names=['x', 'y'])
        names = testing_options['objects'][0].columns.tolist()
        names[0] = 'invalid'
        with pytest.raises(RuntimeError):
            instance.apply_field_names(testing_options['objects'][0],
                                       field_names=names)

    def test_func_serialize_errors(self, instance):
        r"""Test errors raised by func_serialize."""
        with pytest.raises(TypeError):
            instance.func_serialize(None)

    def test_deserialize_no_header(self, instance, testing_options,
                                   python_class, map_sent2recv, options):
        r"""Test deserialization of frame output without a header."""
        if options.get('no_header', False):
            return
        kws = instance.get_testing_options(no_header=True)
        kws['kwargs'].pop('no_header', None)
        no_head_inst = python_class(**kws['kwargs'])
        x = no_head_inst.serialize(kws['objects'][0])
        y = instance.deserialize(x)[0]
        assert(y == map_sent2recv(testing_options['objects'][0]))
